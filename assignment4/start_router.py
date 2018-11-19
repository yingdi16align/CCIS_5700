import sys
import router

config_filename = sys.argv[1]

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print ('Usage: python start_router.py '+config_filename)
    sys.exit(1)

  try:
    r = router.Router(config_filename)
    r.start()
  finally:
    if r: r.stop()
