import argparse
import json
import math
import numpy as np
import os
import requests

from concurrent.futures import ThreadPoolExecutor
from slugify import slugify
from tqdm import tqdm


def parse_arguments():
    parser = argparse.ArgumentParser(description="Pull images for unis")
    parser.add_argument(
        "--uni_file",
        type=str,
        default="unis.json",
        help="File to use for uni names",
    )

    parser.add_argument(
        "--uni_starting_idx",
        type=int,
        default=0,
        help="Starting index of universities to pull images for",
    )

    parser.add_argument(
        "--n_unis",
        type=int,
        default=25,
        help="Number of universities to pull images for",
    )

    parser.add_argument(
        "--img_dir",
        type=str,
        default="imgs",
        help="Where to save all the images",
    )

    parser.add_argument(
        "--num_points",
        type=int,
        default=1000,
        help="Number of points to generate per university",
    )

    return parser.parse_args()


def get_university_bounds(uni, api_key):
    # Format the URL
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    full_uni_name = f"{uni['name']} Main Campus"
    params = {"address": f"{full_uni_name}", "key": api_key}

    # Make the request
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            # Get the viewport bounds
            viewport = data["results"][0]["geometry"]["viewport"]
            return viewport

    return None


def generate_points_in_grid(top_left, bottom_right, num_points):
    """Generate a grid of points within a rectangle"""
    lat1, lng1 = top_left
    lat2, lng2 = bottom_right

    # Calculate grid dimensions that give us closest to num_points
    # For a grid, we want roughly equal spacing in both directions
    grid_size = math.isqrt(num_points)  # This gives us the floor of the square root
    if grid_size * grid_size < num_points:
        grid_size += 1

    # Create an evenly spaced grid
    lats = np.linspace(lat1, lat2, num=grid_size)
    lngs = np.linspace(lng1, lng2, num=grid_size)

    points = []
    for lat in lats:
        for lng in lngs:
            points.append((lat, lng))

    return points


def check_location(args):
    lat, lon, key = args
    mr = requests.get(
        f"https://maps.googleapis.com/maps/api/streetview/metadata?size=400x400&location={lat},{lon}&key={key}"
    )
    if mr.json()["status"] == "ZERO_RESULTS" or "error_message" in mr.json():
        return None
    return (lat, lon)


def get_valid_locations(args_tuple):
    uni, key, args = args_tuple
    # Get bounds of university
    bounds = get_university_bounds(uni, key)
    if not bounds:
        return []

    northeast = bounds["northeast"]  # {lat: xx, lng: xx}
    southwest = bounds["southwest"]  # {lat: xx, lng: xx}
    c1 = (northeast["lat"], northeast["lng"])
    c2 = (southwest["lat"], southwest["lng"])

    # First generate the grid points
    points = generate_points_in_grid(c1, c2, args.num_points)

    # Then check them in parallel
    with ThreadPoolExecutor() as executor:
        arg_tuples = [(lat, lon, key) for lat, lon in points]
        results = list(executor.map(check_location, arg_tuples))

    return [r for r in results if r is not None]


def get_all_uni_points(unis, key, args):
    with ThreadPoolExecutor() as executor:
        arg_tuples = [(uni, key, args) for uni in unis]
        results = list(
            tqdm(
                executor.map(get_valid_locations, arg_tuples),
                total=len(unis),
                desc="Pulling university points",
            )
        )
    return results


def pull_image(args_tuple):
    uni_name, lat, lon, key = args_tuple
    pr = requests.get(
        f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&key={key}"
    )

    with open(f"imgs/{uni_name}/{lat},{lon}.jpg", "wb") as file:
        file.write(pr.content)


def pull_uni_imgs(args_tuple):
    uni, points, key, args = args_tuple

    slug_name = slugify(uni["name"])
    uni_folder_name = f"{args.img_dir}/{slug_name}/"

    # Don't re-pull images from a school you've already done
    if not os.path.exists(uni_folder_name):
        os.makedirs(uni_folder_name)
    else:
        return

    print(slug_name, len(points))

    with ThreadPoolExecutor() as executor:
        args_tuple = [(slug_name, lat, lon, key) for lat, lon in points]
        executor.map(pull_image, args_tuple)


def get_all_uni_images(unis, uni_points, api_key, args):
    os.makedirs(args.img_dir, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        arg_tuples = [
            (uni, points, api_key, args) for uni, points in zip(unis, uni_points)
        ]
        tqdm(
            executor.map(pull_uni_imgs, arg_tuples),
            total=len(unis),
            desc="Pulling university images",
        )


if __name__ == "__main__":
    args = parse_arguments()

    try:
        api_key = os.environ["GOOGLE_MAPS_API_KEY"]
        print(f"Using API key {api_key}")
    except KeyError as e:
        print("Error: Must set GOOGLE_MAPS_API_KEY system environment")
        exit()

    if os.path.isfile(args.uni_file):
        with open(args.uni_file, "r") as f:
            unis = json.load(f)
    else:
        print(f'Error: Uni list "{args.uni_file}" doesn\'t exist')
        exit()

    unis = unis[args.uni_starting_idx : args.uni_starting_idx + args.n_unis]
    uni_points = get_all_uni_points(unis, api_key, args)
    print(f"Got {len(uni_points)} universities!")
    get_all_uni_images(unis, uni_points, api_key, args)

    # Go through and clean out all folders that don't have any images
    for folder in os.listdir(args.img_dir):
        if len(os.listdir(f"{args.img_dir}/{folder}")) == 0:
            os.rmdir(f"{args.img_dir}/{folder}")

    print("Pulled all images!")
