from QGISGridMaker import GridMakerFactory

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", "-c", required=True, help="Client ID")
    parser.add_argument("--project", "-p", required=True, help="Project ID")
    parser.add_argument("--stand", "-s", required=True, help="Stand 3-Digit ID", nargs="+")
    args = parser.parse_args()

    GridMakerFactory(args.client, args.project, args.stand, msg=True)