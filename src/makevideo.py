import os
import sys
import json
import upload_video
import makevideo_helper

from enum import Enum
from apiclient.errors import HttpError
from oauth2client.tools import argparser

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

def upload_to_youtube(upload, vid_out_file, section, hndl, interval):
    if upload:
        sys.stdout.write("UPLOADING video: %s\n" % vid_out_file)
        args.file = vid_out_file
        
        if interval == makevideo_helper.VALID_INTERVAL_STATUSES[0]:
            args.title = "Vine Compilation " + section + " " + \
                                                        str(hndl.FLDR_DATES[0])
        elif interval == makevideo_helper.VALID_INTERVAL_STATUSES[1]:
            args.title = "Vine Compilation " + section + " " + \
                        str(hndl.FLDR_DATES[0]) + "_" + str(hndl.FLDR_DATES[-1])
        elif interval == makevideo_helper.VALID_INTERVAL_STATUSES[2]:
            args.title = "Vine Compilation " + section + " " + \
                                                    str(hndl.FLDR_DATES[0])[:-3]

        args.description = retreive_youtube_description(sect, hndl)

        if section == "COMEDY":
            args.category = "23"
        elif section == "SPORTS":
            args.category = "17"

        args.privacyStatus = "private"
 
        youtube = upload_video.get_authenticated_service(args)
        try:
            upload_video.initialize_upload(youtube, args)
        except HttpError, e:
            print "An HTTP error %d occurred:\n%s" % (e.resp.status, \
                                                                e.content)
    else:
        sys.stdout.write("NOT UPLOADING video: %s\n" % vid_out_file)

def retreive_youtube_description(sect, hndl):
    desc_loc = os.path.join("../descriptions", sect.lower() + '_description.txt')
    with open(desc_loc, 'r') as myfile:
        data = myfile.read()
 
    datafolderloc = os.path.join(makevideo_helper.SECTIONS_PATH, sect, \
                                                'data', str(hndl.FLDR_DATES))
    for _, _, filenames in os.walk(datafolderloc):
        for item in filenames:
            with open(os.path.join(datafolderloc, item)) as json_file:
                    json_data = json.load(json_file)
 
            data = data + json_data["shareUrl"] + '\n'
 
    return data

def retreive_youtube_tags():
    with open("tags.txt", 'r') as myfile:
        data = myfile.read()
 
    return data

if __name__ == "__main__":
    argparser.add_argument("--file", dest='file', help="Video file to upload")
    argparser.add_argument("--title", dest='title', help="Video title")
    argparser.add_argument("--description", dest='description', \
                                                    help="Video description")
    argparser.add_argument("--category", dest='category', default="22",
                                        help="Numeric video category. " +
                                        "See https://developers.google.com/" \
                                        "youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", dest='keywords', \
                                        help="Video keywords, comma separated")
    argparser.add_argument("--privacyStatus", dest='privacyStatus', \
                               choices=upload_video.VALID_PRIVACY_STATUSES,
                               default=upload_video.VALID_PRIVACY_STATUSES[0], \
                               help="Video privacy status.")
    argparser.add_argument('--upload', dest='upload', action='store_true', \
                                help="Will upload video to YouTube if used.")
    argparser.add_argument('--skipbuild', dest='skipbuild', \
               action='store_true', help="Will skip the video build if used.")
    argparser.add_argument("--interval", dest='interval', \
                        choices=makevideo_helper.VALID_INTERVAL_STATUSES, \
                        default=makevideo_helper.VALID_INTERVAL_STATUSES[0], \
                        help="Choices for interval of video for video build.")
    argparser.add_argument('--backdate', dest='backdate', \
                                default=1, help="How far to go back in dates.")
    argparser.add_argument('--section', required=True, dest='section', \
                                help="Select the section to make video from.")
    args = argparser.parse_args()

    MVH = makevideo_helper.MakeVideoHelper(args)

    for sect in MVH.LISTSECTIONS:
        if not args.skipbuild:
            sys.stdout.write("Starting build for %s video\n" % sect)

            if args.interval == makevideo_helper.VALID_INTERVAL_STATUSES[0]:
                vid_out_file = MVH.build__videos(sect, args.skipbuild, \
                                 makevideo_helper.VALID_INTERVAL_STATUSES[0])
            elif args.interval == makevideo_helper.VALID_INTERVAL_STATUSES[1]:
                vid_out_file = MVH.build__videos(sect, args.skipbuild, \
                                 makevideo_helper.VALID_INTERVAL_STATUSES[1])
            elif args.interval == makevideo_helper.VALID_INTERVAL_STATUSES[2]:
                vid_out_file = MVH.build__videos(sect, args.skipbuild, \
                                 makevideo_helper.VALID_INTERVAL_STATUSES[2])

            sys.stdout.write("Finished build for %s video\n" % sect)
        else:
            vid_out_file = MVH.vid_build_name(sect, args.interval)

        upload_to_youtube(args.upload, vid_out_file, sect, MVH, args.interval)

