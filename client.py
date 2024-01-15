from QGISGridMaker.gridmaker import FromIDs

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", "-c", required=True, help="Client ID")
    parser.add_argument("--project", "-p", required=True, help="Project ID")
    parser.add_argument("--stand", "-s", required=True, help="Stand 3-Digit ID", nargs="+")
    args = parser.parse_args()

    for stand in args.stand:
        msg = f"""
        Starting {args.client}, {args.project}, {stand} 
        """
        print(msg)
        FromIDs(args.client, args.project, stand)