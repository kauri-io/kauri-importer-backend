#old main

import os
import sys
import argparse
import easygui

from user.userbase import Community
from builder.docbase import Builder
from builder.backend.mkdocs import MkDocsBuilder
from builder.backend.wordpress import WpConverter

def main():
    args = parser.parse_args()

    # gather information about the github repo being imported
    if args.retrieve:
        print('Retrieving your documentation now.')

        # authentication potentially required here

        # 1) clone repo
        # 2) traverse for .md files
        # 3) copy markdown files to target folder

        community = Community(args.retrieve)

        builder = Builder(args.retrieve)
        print(builder.proj_dir)


    elif args.wpfile:
        path = easygui.fileopenbox()
        wpContent = WpConverter(path)
        print(wpContent)
    else:
        # handle error since no other builders
        print('Your documentation is not supported yet.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='host docs on kauri'
    )
    parser.add_argument(
        '-r',
        dest='retrieve',
        help='retrieve your documentation',
    )
    parser.add_argument(
        '-w',
        dest='wpfile',
        help ='import your wordpress xml file',
    )
    parser.add_argument(
        '-b',
        dest='bridge',
        help='bridge your documentation to Kauri',
    )
    main()
