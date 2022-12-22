from pathlib import Path
from collections import deque
from typing import Optional
# from mat_tools import mat_flu

from .plot import Plotter
from .utils import get_path_descriptor, check_if_target, cprint


# TODO: Use the databases for calibration
# TODO: Also make the CAL-CAL calibration?
def calibrate_fits_files(root_dir: Path, tar_dir: Path,
                         cal_dir: Path, mode_name: str) -> None:
    """The calibration for a target and a calibrator folder

    Parameters
    ----------
    tar_dir: Path
        A specific directory to be the target for calibration
    cal_dir: Path
        A specific directory to be the calibrator for calibration
    mode: str
        The mode of calibration. Either "corrflux", "flux" or "both" depending
        if it is "coherent" or "incoherent" reduced data

    See Also
    --------
    get_path_descriptor()
    """
    cprint(f"Calibrating {tar_dir.name} with {cal_dir.name}", "p")
    targets = tar_dir.glob("TARGET_RAW_INT*")

    if not targets:
        cprint("'TARGET_RAW_INT*'-files found. SKIPPED!", "y")
        print("------------------------------------------------------------")
        return

    targets.sort(key=lambda x: x[-8:])
    calibrators = cal_dir.glob("CALIB_RAW_INT*")
    calibrators.sort(key=lambda x: x[-8:])

    if len(targets) != len(calibrators):
        cprint("#'TARGET_RAW_INT'-files != #'CALIB_RAW_INT'-"\
                      " files. SKIPPING!", "y")
        print("------------------------------------------------------------")
        return

    output_dir = get_path_descriptor(root_dir, "TAR-CAL",
                                     targets[0], calibrators[0])
    mode = "incoherent" if "incoherent" in output_dir else "coherent"
    if not output_dir.exists():
        output_dir.mkdir()

    # TODO: Fix the numbering of the (.fits)-files
    for index, (target, calibrator) in enumerate(zip(targets, calibrators)):
        print("------------------------------------------------------------")
        cprint(f"Processing {target.name} with {calibrator.name}", "g")
        output_file = output_dir / f"TARGET_CAL_INT_000{index+1}.fits"

        fluxcal(target, calibrator, output_file,\
                DATABASE_PATHS, mode=mode_name,
                output_fig_dir=output_dir)

    print("------------------------------------------------------------")
    print("Creating plots...")
    fits_files = output_dir.glob("*.fits")
    for fits_file in fits_files:
        lband = True if "HAWAII" in target else False
        plot_fits = Plotter([fits_file], lband=lband, save_path=output_dir)
        plot_fits.add_cphases().add_corr_flux()
        if (mode == "incoherent") and (plot_fits.flux is not None):
            plot_fits.add_flux()
        plot_fits.plot(save=True)
    print("Plots created!")
    print("------------------------------------------------------------")
    print("Done!")
    print("------------------------------------------------------------")


def calibrate_folders(root_dir: Path, band_dir: Path,
                      mode_name: Optional[str] = "corrflux") -> None:
    """Takes two folders and calibrates their contents together

    Parameters
    ----------
    root_dir: Path
        The path to multiple folders that need to be cross correlated. Will be
        skipped if folders for targets and calibrators are specified
    mode: str, optional
        The mode of calibration. Either "corrflux", "flux" or "both" depending
        if it is "coherent" or "incoherent". Default mode is "corrflux"
    """
    sub_dirs = (root_dir / band_dir).glob("*.rb")
    sub_dirs.sort(key=lambda x: x.split(".")[~2])
    sub_dirs_rotated = deque(sub_dirs.copy())
    sub_dirs_rotated.rotate(1)

    for directory in sub_dirs:
        cprint(f"Calibration of {directory.name} with mode_name={mode_name}", "lp")
        cprint("------------------------------------------------------------", "lg")
        if check_if_target(directory):
            for dir_rotated in sub_dirs_rotated:
                calibrate_fits_files(root_dir, directory,
                                     dir_rotated, mode_name=mode_name)
        else:
            cprint("No 'TARGET_RAW_INT*'-files found. SKIPPED!", "y")
            cprint("------------------------------------------------------------",
                   "lg")
            continue


def calibrate(data_dir: Path, stem_dir: Path, target_dir: Path):
    """Does the full calibration for all of the "cal_dir" subdirectories

    Parameters
    ----------
    data_dir: Path
    stem_dir: Path
    target_dir: Path
    """
    root_dir = Path(data_dir, stem_dir, "products", target_dir)
    modes, bands = {"coherent": "corrflux", "incoherent": "flux"}, ["lband", "nband"]

    for mode, mode_name in modes.items():
        for band in bands:
            band_dir = mode / band
            calibrate_folders(root_dir, band_dir, mode_name=mode_name)
    cprint("Calibration Done!", "lp")


if __name__ == "__main__":
    data_dir = "/data/beegfs/astro-storage/groups/matisse/scheuck/data/"
    stem_dir, target_dir = "matisse/GTO/hd163296/", "ATs/20190323"
    calibrate(data_dir, stem_dir, target_dir)
