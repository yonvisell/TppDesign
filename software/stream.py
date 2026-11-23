"""Newest observation wins while one OSC transaction is in progress per physical unit."""
from threading import Condition,Thread
from time import monotonic

class Latest:
    def __init__(self,client,report):
        self.client=client;self.report=report;self.pending=None;self.last=-float("inf")
        self.closed=False;self.condition=Condition()
        self.worker=Thread(target=self._run,daemon=True);self.worker.start()

    def submit(self,ms,levels,observed):
        # Validate before displacing a previous event or entering the worker.
        from .client import pattern
        pattern(self.client.path,ms,levels)
        if observed!=observed or observed>monotonic():raise ValueError("future or invalid observation")
        with self.condition:
            if self.closed or observed<=self.last:raise ValueError("closed or out-of-order stream")
            self.last=observed
            old=self.pending;self.pending=(ms,dict(levels),observed);self.condition.notify()
        if old:self.report(old[2],dict(outcome="superseded"))

    def _run(self):
        while True:
            with self.condition:
                while self.pending is None and not self.closed:self.condition.wait()
                if self.pending is None:return
                ms,levels,t=self.pending;self.pending=None
            try:result=self.client.pattern(ms,levels,observed=t)
            except (OSError,ValueError,OverflowError) as error:result=dict(outcome="no_confirmed_receipt",detail=str(error))
            self.report(t,result)

    def close(self):
        with self.condition:self.closed=True;self.condition.notify_all()
        self.worker.join()
