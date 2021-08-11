import os, sys

link = sys.argv[1]

print("Starting download of " + link)

os.system("youtube-dl --extract-audio --audio-format mp3 " + link)

print("----------\nAll downloads done. Renaming files.\n----------")
_, _, filenames = next(os.walk("."))

for fn in filenames:
    if "-" in fn and "mp3" in fn:
        old = fn
        parts = fn.split("-")
        new = "".join(parts.pop())
        print("Moving " + old + " to: " + new)
        os.rename(old, new)

os.system("mv *.mp3 music/.")
print("All done!")
