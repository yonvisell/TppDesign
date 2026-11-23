"""Give GCC stable source paths and build dates in reproducible ESP32-C6 artifacts."""
import os
Import("env")
# Release date at 00:00 UTC. GCC honors SOURCE_DATE_EPOCH for __DATE__/__TIME__.
epoch = "1795392000"
env["ENV"]["SOURCE_DATE_EPOCH"] = epoch
os.environ["SOURCE_DATE_EPOCH"] = epoch
for variable, label in [("$PROJECT_DIR","/tpp-r2j"),("$BUILD_DIR","/tpp-build")]:
    path = env.subst(variable)
    env.Append(CCFLAGS=["-ffile-prefix-map=" + path + "=" + label])
# Library assertion strings include the configured cache spelling on macOS.
# Normalize both the configured path and the OS-resolved alias in GCC output.
packages = os.path.dirname(env.PioPlatform().get_package_dir("framework-arduinoespressif32"))
for path in sorted({packages, os.path.realpath(packages)}):
    env.Append(CCFLAGS=["-ffile-prefix-map=" + path + "=/tpp-packages"])
