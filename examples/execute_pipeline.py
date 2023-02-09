from pathlib import Path

from matadrs import reduction_pipeline


# Specify the path to the directory containing the data
data_dir = Path("/data/beegfs/astro-storage/groups/matisse/scheuck/data/matisse/GTO/hd163296")
observation_dirs = ["2019-03-22"]

# Speficy the raw-directory, containing the raw data
raw_dirs = list(map(lambda x: data_dir / "raw" / x, observation_dirs))

# Speficy the product-directory, to contain the product data/that contains reduced,
# calibrated or averaged data, to be further processed
product_dirs = list(map(lambda x: Path(str(x).replace("raw", "product")), raw_dirs))

# Call the reduction_pipeline
reduction_pipeline(raw_dirs, product_dirs, overwrite=True, do_reduce=False,
                   do_calibrate=True, do_average=True, do_merge=True)
