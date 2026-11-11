import argparse
import logging
import sys

from app.jobs import GRUPOS, ejecutar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

parser = argparse.ArgumentParser(prog="python -m app.jobs")
parser.add_argument("grupo", choices=GRUPOS)
parser.add_argument("--solo", help="ejecuta solo la tarea con este nombre")
args = parser.parse_args()

sys.exit(1 if ejecutar(args.grupo, args.solo) else 0)
