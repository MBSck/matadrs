"""

Routine
-------

See Also
--------

References
----------

Examples
--------
"""

__all__ = ["copy_calibrated_files", "average_files", "average_folders", "average"]

import shutil
from pathlib import Path
from typing import Optional

from .avg_oifits import avg_oifits
from ..utils.plot import Plotter
from ..utils.tools import cprint, split_fits, get_fits_by_tag, get_execution_modes


HEADER_TO_REMOVE = [{'key': 'HIERARCH ESO INS BCD1 ID', 'value': ' '},
                    {'key': 'HIERARCH ESO INS BCD2 ID', 'value': ' '},
                    {'key': 'HIERARCH ESO INS BCD1 NAME', 'value': ' '},
                    {'key': 'HIERARCH ESO INS BCD2 NAME', 'value': ' '}]


def copy_calibrated_files(directory: Path, output_dir: Path) -> None:
    """Copies the bcd-calibrated files to the averaged directory

    Parameters
    ----------
    directory: Path
        The directory to be searched in
    output_dir: Path
        The directory to which the new files are saved to
    """
    bcd_pip_files = get_fits_by_tag(directory, "CAL_INT_noBCD")
    bcd_files = get_fits_by_tag(directory, "BCD_CAL")
    for bcd_pip_file, bcd_file in zip(bcd_pip_files, bcd_files):
        shutil.copy(str(bcd_pip_file), (output_dir / bcd_pip_file.name))
        shutil.copy(str(bcd_file), (output_dir / bcd_file.name))


def average_files(directory: Path, file_type: str, output_dir: Path) -> None:
    """Averages the unchopped (.fits)-files and the chopped (.fits)-files if given

    Parameters
    ----------
    directory: Path
        The directory to be searched in
    file_type: str
        Either 'flux' or 'vis' for the flux and visibility calibration, respectively
    output_dir: Path
        The directory to which the new files are saved to

    Notes
    -----
    This creates either one or two output files depending if there are only unchopped or
    also chopped files. The files' names are with either 'INT' or 'INT_CHOPPED',
    respectively, and indicated that they are averaged by an 'AVG' in their name


    See also
    --------
    .avg_oifits.avg_oifits: Averaging for (.fits)-files
    """
    if file_type == "flux":
        cprint("Averaging flux calibration...", "g")
        outfile_name = "TARGET_AVG_FLUX"
        unchopped_fits, chopped_fits = split_fits(directory, "TARGET_FLUX_CAL")
    else:
        cprint("Averaging visibility calibration...", "g")
        unchopped_fits, chopped_fits = split_fits(directory, "TARGET_CAL")
        outfile_name = "TARGET_AVG_VIS"

    outfile_unchopped = output_dir / f"{outfile_name}_INT.fits"
    avg_oifits(unchopped_fits, outfile_unchopped, headerval=HEADER_TO_REMOVE)

    if chopped_fits is not None:
        outfile_chopped = output_dir / f"{outfile_name}_INT_CHOPPED.fits"
        avg_oifits(chopped_fits, outfile_chopped, headerval=HEADER_TO_REMOVE)


def average_folders(calibrated_dir: Path, mode: str) -> None:
        """Iterates over the calibrated directories to

        Parameters
        ----------
        calibrated_dir: Path
            The directory containing the calibration's products
        mode: str, optional
            The mode in which the reduction is to be executed. Either 'coherent',
            'incoherent' or 'both'
        """
        for directory in (calibrated_dir / "calib" / mode).glob("*.rb"):
            cprint(f"Averaging folder {directory.name}...", "g")
            cprint(f"{'':-^50}", "lg")

            folder_split = directory.name.split(".")
            folder_split[0] += "-AVG"
            new_folder = ".".join(folder_split)
            output_dir = calibrated_dir / "averaged" / mode / new_folder

            if not output_dir.exists():
                output_dir.mkdir(parents=True)

            average_files(directory, "flux", output_dir)
            average_files(directory, "vis", output_dir)
            copy_calibrated_files(directory, output_dir)

            cprint("Plotting averaged files...", "g")
            for fits_file in get_fits_by_tag(output_dir, "AVG"):
                plot_fits = Plotter([fits_file], save_path=output_dir)
                plot_fits.add_cphases().add_vis().plot(save=True)
            cprint(f"{'':-^50}", "lg")


# TODO: Implement overwrite
def average(calibrated_dir: Path,
            mode: Optional[str] = "both", overwrite: Optional[bool] = False):
    """Does the full averaging for all of the calibrated directories subdirectories

    Parameters
    ----------
    calibrated_dir: Path
        The directory containing the calibration's products
    mode: str, optional
        The mode in which the reduction is to be executed. Either 'coherent',
        'incoherent' or 'both'
    overwrite: bool, optional
        If 'True' overwrites present files from previous calibration
    """
    for mode in get_execution_modes(mode)[0]:
        cprint("Averaging and BCD-calibration of"
               f" {calibrated_dir.name} with mode={mode}", "lp")
        cprint(f"{'':-^50}", "lg")
        average_folders(calibrated_dir, mode)
    cprint("Averaging done!", "lp")
    cprint(f"{'':-^50}", "lg")