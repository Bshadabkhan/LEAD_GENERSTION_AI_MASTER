import gerbonara

print("\n--- help(gerbonara.rs274x) ---")
try:
    help(gerbonara.rs274x)
except AttributeError:
    print("gerbonara.rs274x not found")

print("\n--- help(gerbonara.ipc356) ---")
try:
    help(gerbonara.ipc356)
except AttributeError:
    print("gerbonara.ipc356 not found")

