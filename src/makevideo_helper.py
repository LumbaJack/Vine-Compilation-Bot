import os
import sys
import time
import json
import random
import urllib
import fnmatch
import datetime
import calendar

from PIL import Image
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, \
                                                                    ImageClip

VALID_INTERVAL_STATUSES = ("daily", "weekly", "monthly")

if os.name == 'nt':
    SECTIONS_PATH = "C:\\Vines\\sections"
else:
    SECTIONS_PATH = "sections"

class MakeVideoHelper(object):
    """ Helper Functions for CSV files """
    def __init__(self, args):
        self.MAXLINE = 44
        self.LISTSECTIONS = [args.section]

        if args.interval == VALID_INTERVAL_STATUSES[0]:
            self.FLDR_DATES = [datetime.date.fromordinal(\
                       datetime.date.today().toordinal() - int(args.backdate))]
            self.PREV_DATES = [datetime.date.fromordinal(\
                 datetime.date.today().toordinal() - (int(args.backdate) + 1))]
        elif args.interval == VALID_INTERVAL_STATUSES[1]:
            thisweek = datetime.date.fromordinal(\
                                       datetime.date.today().toordinal() - 7)
            self.FLDR_DATES = sorted([thisweek + datetime.timedelta(days=i) \
                                        for i in range(0 - thisweek.weekday(), \
                                                       7 - thisweek.weekday())])
            lastweek = datetime.date.fromordinal(\
                                       datetime.date.today().toordinal() - 14)
            self.PREV_DATES = sorted([lastweek + datetime.timedelta(days=i) \
                                        for i in range(0 - lastweek.weekday(), \
                                                       7 - lastweek.weekday())])
        elif args.interval == VALID_INTERVAL_STATUSES[2]:
            thismonth = datetime.date.fromordinal(\
                                       datetime.date.today().toordinal() - 28)
            num_days = calendar.monthrange(thismonth.year, thismonth.month)[1]
            self.FLDR_DATES = sorted([datetime.date(thismonth.year, \
                        thismonth.month, day) for day in range(1, num_days+1)])

            lastmonth = datetime.date.fromordinal(\
                                       datetime.date.today().toordinal() - 56)
            num_days = calendar.monthrange(lastmonth.year, lastmonth.month)[1]
            self.PREV_DATES = sorted([datetime.date(lastmonth.year, \
                        lastmonth.month, day) for day in range(1, num_days+1)])
    
    def build__videos(self, option, skipbuild, interval):
        # video output file name
        vid_out_file = self.vid_build_name(option, interval)
     
        # build the vine compilation
        if not skipbuild:
            clips = []
         
            # add the intro
            intro = self.add_intro()
            clips.append(intro)
            currloc = intro.duration
         
            # generate list of all available vids
            (tmpclips, currloc, totalcliptime) = self.generate_vid_list(\
                                                                option, currloc)
          
            # set the background image
            clip= self.add_background(intro, totalcliptime)
            clips.append(clip)
              
            # add list of individual vids
            clips.extend(tmpclips)
          
            # add the outro
            outro = self.add_outro(currloc)
            clips.append(outro)
              
            # add previous days best video to outro
            best_vid_clip = self.get_previous_bests_vid(option, currloc)
            clips.append(best_vid_clip)
          
            # finalize the video file
            final_clip = CompositeVideoClip(clips, size=(1920,1080))
            final_clip.fps=30
            final_clip.write_videofile(vid_out_file)

        return vid_out_file
    
    def add_intro(self):
        for _, _, filenames in os.walk('../intros'):
            choice = os.path.join("../intros", random.choice(filenames))
            sys.stdout.write("Adding intro: %s\n" % choice)
            clip = VideoFileClip(choice)
            clip = clip.set_start(0)
 
        return clip

    def generate_vid_list(self, option, currloc):
        tmpclips = []
        totalcliptime = 0

        for fldr_date in self.FLDR_DATES:
            folderloc = os.path.join(SECTIONS_PATH, option, 'videos', \
                                                                str(fldr_date))
            datafolderloc = os.path.join(SECTIONS_PATH, option, 'data', \
                                                                str(fldr_date))
         
            for root, _, filenames in os.walk(folderloc):
                for filename in fnmatch.filter(filenames, '*.mp4'):
                    datavar = filename.split('.')[0]
                    dname = os.path.join(datafolderloc, datavar + ".json")
                    if not os.path.isfile(dname):
                        sys.stderr.write("ERROR: no data found for: %s\n" % \
                                                                        dname)
                        continue
                    else:
                        with open(dname) as json_file:
                            json_data = json.load(json_file)
         
                    if self.check_blacklisted_users(json_data["username"]):
                        continue
                    
                    fname = os.path.join(root, filename)
                    if not os.path.isfile(fname):
                        sys.stderr.write("ERROR: no video found for: %s\n" % \
                                                                        fname)
                        continue 
                    else:
                        sys.stdout.write("Adding file name: %s\n" % \
                                                fname[len(SECTIONS_PATH)+1:])
         
                    try:
                        clip = (VideoFileClip(fname).resize((1157, 830)).\
                                            set_start(currloc).crossfadein(1).\
                                            set_position("center").\
                                            set_position((383, 88)))
                    except:
                        sys.stderr.write("ERROR: cannot open video: %s\n" % \
                                                                        fname)
         
                        sys.stderr.write("DELETING: %s\n" % fname)
                        os.remove(fname)
                        sys.stderr.write("DELETING: %s\n" % dname)
                        os.remove(dname)
                        continue
         
                    tmpclips.append(clip)
                     
                    # add creator image
                    self.make_creator_icon(json_data["avatarUrl"], \
                                                            datavar + ".jpg")
                    creatorclip = (ImageClip(datavar + ".jpg", \
                                         transparent=True).set_start(currloc).\
                                         set_duration(clip.duration).\
                                         set_position((383, 10)))
         
                    tmpclips.append(creatorclip)
                    time.sleep(1)
                    os.remove(datavar + ".jpg")
                     
                    # add creator name
                    try:
                        creatortxt = TextClip(json_data["username"].encode(\
                                       'ascii', 'ignore'), font='Arial-Black', \
                                        color="MediumSpringGreen", fontsize=30)
                    except:
                        sys.stderr.write("\nERROR: using default username.\n")
                        creatortxt = TextClip("Default UserName", \
                                                  font='Arial-Black', \
                                                  color="MediumSpringGreen", \
                                                  fontsize=30)

                    creatortxt_col = creatortxt.on_color(col_opacity=0).\
                                                set_duration(clip.duration).\
                                                set_start(currloc)
         
                    creatortxt_mov = creatortxt_col.set_position((465, 23))
                    tmpclips.append(creatortxt_mov)
         
                    # add the description
                    desc_clip = self.create_description(\
                                        json_data["description"], currloc, clip)
                    for item in desc_clip:
                        tmpclips.append(item)
         
                    currloc += clip.duration
                    totalcliptime += clip.duration
     
        return (tmpclips, currloc, totalcliptime)

    def make_creator_icon(self, avatarUrl, imgname):
        try:
            urllib.urlretrieve(avatarUrl, imgname)
            im = Image.open(imgname)
            im.thumbnail((72,72), Image.ANTIALIAS)
            im.save(imgname, "JPEG")
        except IOError:
            sys.stderr.write("ERROR: using default creator photo.\n")
            urllib.urlretrieve("http://i288.photobucket.com/albums/ll173/" \
                              "sophia_wright1/icon_zpsudc5pfpa.jpg", imgname)

    def create_description(self, description, currloc, clip):
        rl = list()

        if not description:
            description = "No Title"
        else:
            description = ' '.join(description.encode('ascii', \
                                                            'ignore').split())
     
        desc_list = self.break_up_description(description)
         
        if len(desc_list) == 1:
            rl.append(self.description_helper(desc_list[0], currloc, 970, clip))
        elif len(desc_list) == 2:
            rl.append(self.description_helper(desc_list[0], currloc, 946, clip))
            rl.append(self.description_helper(desc_list[1], currloc, 994, clip))
        elif len(desc_list):
            rl.append(self.description_helper(desc_list[0], currloc, 925, clip))
            rl.append(self.description_helper(desc_list[1], currloc, 970, clip))
            rl.append(self.description_helper(desc_list[2], \
                                                        currloc, 1015, clip))
         
        return rl

    def break_up_description(self, description):
        tempstr = ""
        desc_list = list()
     
        for idx, item in enumerate(description.split()):
            if not len(tempstr):
                tempstr = item
            elif len(tempstr) + len(item) + 1 < self.MAXLINE:
                tempstr = tempstr + " " + item
            else:
                desc_list.append(tempstr)
                tempstr = item
     
            if tempstr and idx == len(description.split()) - 1:
                desc_list.append(tempstr)
         
        return desc_list

    def description_helper(self, description, currloc, position, clip):
        txt = TextClip(description, font='Arial', color="MediumSpringGreen", \
                                                                    fontsize=44)
        txt_col = txt.on_color(col_opacity=0).set_duration(clip.duration).\
                                                            set_start(currloc)
         
        txt_mov = txt_col.set_position(('center', position))
         
        return txt_mov

    def add_background(self, intro, totalcliptime):
        for _, _, filenames in os.walk('../backgrounds'):
            choice = os.path.join("../backgrounds", random.choice(filenames))
            sys.stdout.write("Adding background: %s\n" % choice)
            clip = (ImageClip(choice, transparent=True).\
                                                    set_start(intro.duration).\
                                                    set_duration(totalcliptime))
     
        return clip

    def add_outro(self, currloc):
        for _, _, filenames in os.walk('../outros'):
            choice = os.path.join("../outros", random.choice(filenames))
            sys.stdout.write("Adding outro: %s\n" % choice)
            clip = (VideoFileClip(choice).set_start(currloc))
     
        return clip

    def get_previous_bests_vid(self, option, currloc):
        dpoint = None
        dpointvidfldr = None

        sys.stdout.write("Searching for previous intervals best vine...\n")
        for prev_date in self.PREV_DATES:
            vidfolderloc = os.path.join(SECTIONS_PATH, option, 'videos', \
                                                                str(prev_date))
            datafolderloc = os.path.join(SECTIONS_PATH, option, 'data', \
                                                                str(prev_date))
         
            for _, _, filenames in os.walk(datafolderloc):
                for idx, item in enumerate(filenames):
                    with open(os.path.join(datafolderloc, item)) as json_file:
                        json_data = json.load(json_file)
         
                    clip = VideoFileClip(os.path.join(vidfolderloc, \
                                          str(json_data["postId"]) + ".mp4"))

                    if clip.duration > 5:
                        if not dpoint:
                            dpoint = json_data
                            dpointvidfldr = vidfolderloc
                        elif dpoint["loops"]["count"] < json_data["loops"]\
                                                                    ["count"]:
                            dpoint = json_data
                            dpointvidfldr = vidfolderloc
                    elif not dpoint and idx == len(filenames) - 1:
                        dpoint = json_data
                        dpointvidfldr = vidfolderloc
     
        vidfile = os.path.join(dpointvidfldr, str(dpoint["postId"]) + ".mp4")
        sys.stdout.write("Adding previous best vid: %s\n" % vidfile)
        clip = (VideoFileClip(vidfile).resize((1070, 640)).\
                                    set_start(currloc + 6).crossfadein(1).\
                                    set_position((450, 255)).set_duration(5))
         
        return clip.without_audio()

    def vid_build_name(self, option, interval):
        if interval == VALID_INTERVAL_STATUSES[0]:
            return option.lower() + "_" + str(self.FLDR_DATES[0]) + ".mp4"
        elif interval == VALID_INTERVAL_STATUSES[1]:
            return option.lower() + "_" + str(self.FLDR_DATES[0]) + \
                                        "_" + str(self.FLDR_DATES[-1]) + ".mp4"
        elif interval == VALID_INTERVAL_STATUSES[2]:
            return option.lower() + "_" + str(self.FLDR_DATES[0])[:-3] + ".mp4"

    def check_blacklisted_users(self, username):
        with open("blacklisted_users.txt", 'r') as myfile:
            users = myfile.read().splitlines()

        if username in users:
            return True

        return False

