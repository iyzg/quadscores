## UniScores

This is a project I'm working on to try and "objectively" classify how pretty universities are with AI! I need help pulling all the images, so here's a quick setup guide if you'd like to help expand this :)

![example score distribution](assets/histogram.png)

## How to contribute!

### Step 1

> $ pip install -r requirements.txt

> $ python pull_images.py --num_points 1000 --uni_starting_idx [X] --n_unis 25

Replace the `[X]` with the first index that hasn't yet been catalogged. As of last update, that index is **20**! You'll also have to set your environment's `GOOGLE_MAPS_API_KEY` variable to be your Google Maps API key. 

Be careful running this script a bunch as it can very quickly eat your credits. One run with these parameters is guaranteed to be under the free monthly quote of $200. 

### Step 2

Once you've done your run, upload the zip files to a Google Colab instance of [this code](texthttps://colab.research.google.com/drive/14U9AMSeie2kBPveaSxrrXpeGixCIzG1_?usp=sharing). This has only been tested with A100s, but should work on smaller GPUs as well.

This should produce a bunch of numpy files `.npy` of the school's scores. Once you have those, download them, and leave an issue letting me know. You're also welcome to make a PR with your scores in the folder and letting me know what `pull_images.py` command you ran so I can update the README with the proper starting index.

### Step 3

Wow, there's no third step! Hopefully, all the code has ran for you, and the school scores you've computed will soon be live on the website!