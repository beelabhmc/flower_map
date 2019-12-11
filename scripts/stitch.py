import argparse
import Metashape

parser = argparse.ArgumentParser(description='Stitch the drone imagery together.')
parser.add_argument(
    "images", nargs="?",
    help="a path to a folder containing the drone imagery to stitch with"
)
parser.add_argument(
    "stitched", type=argparse.FileType('w', encoding='UTF-8'),
    default=sys.stdout, help="the stitched orthomosaic, as a metashape project file"
)
args = parser.parse_args()
