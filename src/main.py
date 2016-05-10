import os
import sys
import time
import json
import urllib
import vineapi

from enum import Enum
from progressbar import Bar, ETA, ReverseBar, ProgressBar

if os.name == 'nt':
    SECTIONS = "C:\\Vines\\sections"
else:
    SECTIONS = "sections"

# dormant options for categories
#CATS = "3"
#DOGS = "4"
#URBAN = "6"
#SPECIALFX = "8"
#HEALTHANDFITNESS = "13"

class daily_constants(Enum):
    COMEDY = "1"
    SPORTS = "9"
    MUSIC = "11"

class weekly_constants(Enum):
    ART = "2"
    FAMILY = "7"
    FOOD = "10"
    NEWS = "14"
    ANIMALS = "17"

class monthly_constants(Enum):
    PLACES = "5"
    STYLE = "12"
    OLDWEIRD = "15"
    OLDSCARY = "16"

def download_video(url, outname):
    vidObj=urllib.FancyURLopener()
    vidObj.retrieve(url, outname)

def handle_videos(section, inputobj, vinehdl):
    datadir = os.path.join(SECTIONS, section.name, "data")
    viddir = os.path.join(SECTIONS, section.name, "videos")

    if not os.path.exists(os.path.join(SECTIONS, section.name)):
        os.makedirs(os.path.join(SECTIONS, section.name))

    for item in inputobj["records"]:        
        # SAVE DATA
        if not os.path.exists(datadir):
            os.makedirs(datadir)

        outdatafile = os.path.join(datadir, item["created"].split('T')[0])
        if not os.path.exists(outdatafile):
            os.makedirs(outdatafile)

        outdatafile = os.path.join(outdatafile, str(item["postId"]) + ".json")
        if not os.path.isfile(outdatafile):
            sys.stdout.write("Saving data to: %s\n" % \
                                                outdatafile[len(SECTIONS)+1:])
            with open(outdatafile, 'w') as file_:
                file_.write(json.dumps(item))
        else:
            sys.stdout.write("Updating data file: %s\n" % \
                                                outdatafile[len(SECTIONS)+1:])
            with open(outdatafile, 'w') as file_:
                file_.write(json.dumps(item))

        # SAVE VIDEO
        if not os.path.exists(viddir):
            os.makedirs(viddir)

        outvidfile = os.path.join(viddir, item["created"].split('T')[0])
        if not os.path.exists(outvidfile):
            os.makedirs(outvidfile)

        outvidfile = os.path.join(outvidfile, str(item["postId"]) + ".mp4")
        if not os.path.isfile(outvidfile):
            sys.stdout.write("Saving video to: %s\n" % \
                                                outvidfile[len(SECTIONS)+1:])
            download_video(item["videoUrl"], outvidfile)
        else:
            sys.stdout.write("Skipping video: %s\n" % \
                                                outvidfile[len(SECTIONS)+1:])

    if inputobj["nextPage"]:
        sys.stdout.write("**** Checking page number: %s ****\n" % \
                                                        inputobj["nextPage"])
        handle_videos(section, vinehdl.timeline_sections(section.value, \
                                            page=inputobj["nextPage"]), vinehdl)

def scrape_function():
    vinehdl = vineapi.Vine()
    vinehdl.login("", "")

    for constants in [daily_constants, weekly_constants, monthly_constants]:
        for section in constants:
            handle_videos(section, vinehdl.timeline_sections(section.value), \
                                                                        vinehdl)

    sys.stdout.write("Done searching for videos.")

if __name__ == "__main__":
    while True:
        scrape_function()

        widgets = [Bar('>'), ' ', ETA(), ' for next run ', ReverseBar('<')]
        pbar = ProgressBar(widgets=widgets, maxval=3600).start()
        for i in range(3600):
            time.sleep(1)
            pbar.update(i+1)
        pbar.finish()
