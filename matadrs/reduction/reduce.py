import os
import shutil
import pkg_resources
from pathlib import Path
from typing import List, Set, Tuple, Union, Optional

import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.table import Table
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord

from ..mat_tools.libAutoPipeline import matisseType
from ..mat_tools.mat_autoPipeline import mat_autoPipeline
from ..utils.plot import Plotter
from ..utils.readout import ReadoutFits
from ..utils.tools import cprint, print_execution_time, capitalise_to_index,\
        get_execution_modes, get_fits_by_tag, move

__all__ = ["get_readout_for_tpl_match", "get_tpl_starts", "in_catalog",
           "get_catalog_match", "prepare_catalogs", "set_script_arguments",
           "cleanup_reduction", "reduce_mode_and_band", "prepare_reduction", "reduce"]


CATALOG_DIR = Path(pkg_resources.resource_filename("matadrs", "data/catalogues"))
JSDC_V2_CATALOG = Vizier(catalog="II/346/jsdc_v2")
JSDC_CATALOG = CATALOG_DIR / "jsdc_v2_catalog_20170303.fits"
ADDITIONAL_CATALOG = CATALOG_DIR / "supplementary_catalog_202207.fits"

SPECTRAL_BINNING = {"low": [5, 7], "high_uts": [5, 38], "high_ats": [5, 98]}


def get_readout_for_tpl_match(raw_dir: Path, tpl_start: str) -> Path:
    """Gets the readout of a singular (.fits)-file matching the 'tpl_start', i.e.,
    the starting time of the observation

    Parameters
    ----------
    raw_dir: Path
        The directory containing the raw-files
    tpl_start: str
        The starting time of the observation

    Returns
    -------
    fits_file: Path
        A (.fits)-file matching the input
    """
    for fits_file in raw_dir.glob("*.fits"):
        readout = ReadoutFits(fits_file)
        if tpl_start == readout.tpl_start:
            return readout
    raise FileNotFoundError(f"No file with matching tpl_start: '{tpl_start}' exists!")


def get_tpl_starts(raw_dir: Path) -> Set[str]:
    """Iterates through all files and gets their 'tpl_start', i.e, the starting time of
    the individual observations

    Parameters
    ----------
    raw_dir: Path
        The directory containing the raw-files

    Returns
    -------
    tpl_starts: Set[str]
        The starting times of all the observations given by the raw-files
    """
    return set([ReadoutFits(fits_file).tpl_start for fits_file in raw_dir.glob("*.fits")])


def find_catalogs(calib_dir: Path) -> List[Path]:
    """Searches for JSDC-catalogs in the provided directory and returns their Paths"""
    return [catalog for catalog in calib_dir.glob("*.fits") if
            matisseType(ReadoutFits(catalog).primary_header) == "JSDC_CAT"]


# TODO: Test if the times are correct
def remove_old_catalogs(catalog: Path, calib_dir: Path):
    """Checks if the latest catalog is already existing in the calibration directory and
    removes outdated iterations

    Parameters
    ----------
    calib_dir: Path
        The directory containing to the observation associated calibration files
    """
    newest_catalog_time = Time(ReadoutFits(catalog).primary_header["DATE"])\
            if "DATE" in ReadoutFits(catalog).primary_header else ""
    for readout in list(map(lambda x: ReadoutFits(x), find_catalogs(calib_dir))):
        catalog_time = Time(readout.primary_header["DATE"])\
                if "DATE" in readout.primary_header else ""
        if (newest_catalog_time and catalog_time):
            if catalog_time < newest_catalog_time:
                cprint("Removing outdated catalog...", "g")
                os.remove(readout.fits_file)
        else:
            cprint("Removing unspecified catalog...", "g")
            os.remove(readout.fits_file)


def in_catalog(readout: ReadoutFits,
               radius: u.arcsec, catalog: Path) -> Optional[Path]:
    """Checks if calibrator is in the given supplementary catalog

    Parameters
    ----------
    readout: ReadoutFits
        A class wrapping a (.fits)-file, that reads out its information
    radius: u.arcsec
        The radius in which targets are queried from the catalog
    catlog: Path
        The catalog which is to be queried from the catalog

    Returns
    -------
    catalog: Path | None
        The catalog in which the object has been found in.
        Returns None if object not found
    """
    table = Table().read(catalog)
    coords_catalog = SkyCoord(table["RAJ2000"], table["DEJ2000"],
                              unit=(u.hourangle, u.deg), frame="icrs")
    separation = readout.coords.separation(coords_catalog)
    if separation[np.nanargmin(separation)] < radius.to(u.deg):
        cprint(f"Calibrator '{readout.name}' found in supplementary catalog!", "g")
        return catalog
    cprint(f"Calibrator '{readout.name}' not found in any catalogs!"
           " No TF2 and the 'mat_cal_oifits'-recipe will fail", "r")
    return None


def get_catalog_match(readout: ReadoutFits,
                      radius: u.arcsec = 20*u.arcsec) -> Union[Path, None]:
    """Checks if the given calibrator is contained in the 'jsdc_v2'-catalog. If otherwise
    searches the local, supplementary calibrator databases instead. If nothing is found
    returns None

    Parameters
    ----------
    readout: ReadoutFits
        A class wrapping a (.fits)-file, that reads out its information
    radius: u.arcsec
        The radius in which targets are queried from the catalog

    Returns
    -------
    catalog: Path | None
        The catalog in which the object has been found in
    """
    match = JSDC_V2_CATALOG.query_region(readout.coords, radius=radius)
    if match:
        if len(match[0]) > 0:
            cprint(f"Calibrator '{match[0]['Name'][0]}' found in JSDC v2 catalog!", "y")
        return JSDC_CATALOG
    return in_catalog(readout.coords, radius=radius, catalog=ADDITIONAL_CATALOG)


# NOTE: Is this function even necessary, it seems like the catalogs of the VLTI are
# anyways newer than the ones online -> Check with Jozsef and check multiple files
def prepare_catalogs(raw_dir: Path, calib_dir: Path, tpl_start: str) -> None:
    """Checks if the starting time given by 'tpl_start' corresponds to the observation of
    a science target/calibrator and removes/prepares the un/needed catalogs

    Parameters
    ----------
    raw_dir: Path
        The direcotry containing the raw observation files
    calib_dir: Path
        The directory containing to the observation associated calibration files
    tpl_start: str
        The starting time of the observation
    """
    readout = get_readout_for_tpl_match(raw_dir, tpl_start)
    if readout.is_calibrator():
        cprint(f"Calibrator '{readout.name}' detected!"
               f" Checking for catalog...", "g")
        catalog = get_catalog_match(readout)
        if catalog is not None:
            remove_old_catalogs(catalog, calib_dir)
            if not find_catalogs(calib_dir):
                cprint(f"Moving catalog to {calib_dir.name}...", "g")
                shutil.copy(catalog, calib_dir / catalog.name)
            else:
                cprint("Latest catalog already present!", "g")
    else:
        for catalog in calib_dir.glob("*catalog*"):
            os.remove(catalog)
        cprint(f"Science target '{readout.name}' detected! Removing catalogs...", "y")


def get_spectral_binning(raw_dir, tpl_start) -> List[int]:
    """Gets the spectral binning according to the integration times used in the
    observation

    Parameters
    ----------
    raw_dir: Path
        The directory containing the raw observation files
    tpl_start: str
        The starting time of the observation

    Returns
    -------
    spectral_binning: List[int]
    """
    readout = get_readout_for_tpl_match(raw_dir, tpl_start)
    if readout.resolution == "high":
        resolution = f"{readout.resolution}_{readout.array_configuration}"
    else:
        resolution = readout.resolution
    return SPECTRAL_BINNING[resolution]


def set_script_arguments(mode: str) -> Tuple[str]:
    """Sets the arguments that are then passed to the 'mat_autoPipeline.py' script

    Parameters
    ----------
    raw_dir: Path
        The directory containing the raw observation files
    mode: str
        The mode in which the reduction is to be executed. Either 'coherent',
        'incoherent' or 'both'
    tpl_start: str
        The starting time of the observation

    Returns
    -------
    lband_params: str
        The additional arguments passed to the `mat_autoPipeline` for the L-band. For the
        rest of the arguments see the `mat_autoPipeline`-script
    nband_params: str
        The additional arguments passed to the `mat_autoPipeline` for the N-band. For the
        rest of the arguments see the `mat_autoPipeline`-script
    """
    coh = "/corrFlux=TRUE/coherentAlgo=2/" if mode == "coherent" else ""
    return coh, f"{coh}/useOpdMod=TRUE/"


def prepare_reduction(raw_dir: Path, calib_dir: Path,
                      product_dir: Path, overwrite: bool) -> None:
    """Prepares the reduction by removing removing old product files and sorting the raw
    files by associated calibrations and observations

    Parameters
    ----------
    raw_dir: Path
        The direcotry containing the raw observation files
    calib_dir: Path
        The directory containing to the observation associated calibration files
    product_dir: Path
        The directory to contain the reduced files
    overwrite: bool, optional
        If 'True' overwrites present files from previous reduction
    """
    if not product_dir.exists():
        product_dir.mkdir(parents=True)
    if not calib_dir.exists():
        calib_dir.mkdir(parents=True)

    cprint("Moving calibration files into 'calib_files' folders...", "g")
    for calibration_file in raw_dir.glob("M.*"):
        shutil.move(calibration_file, calib_dir / calibration_file.name)


def cleanup_reduction(product_dir: Path, mode: str,
                      band: str, overwrite: bool) -> None:
    """Moves the folders to their corresponding folders of structure '/mode/band' after
    the reduction has been finished and plots the (.fits)-files contained in them

    Parameters
    ----------
    mode: str, optional
        The mode in which the reduction is to be executed. Either 'coherent',
        'incoherent' or 'both'
    band: str, optional
        The band in which the reduction is to be executed. Either 'lband',
        'nband' or 'both'
    overwrite: bool, optional
        If 'True' overwrites present files from previous reduction
    """
    mode_and_band_dir = product_dir / mode / band
    if not mode_and_band_dir.exists():
        mode_and_band_dir.mkdir(parents=True)

    for reduced_folder in product_dir.glob("Iter1/*.rb"):
        cprint(f"Moving folder '{reduced_folder.name}'...", "g")
        move(reduced_folder, mode_and_band_dir, overwrite)

    # TODO: Remove this for loop? Maybe after properly implementing plotting?
    for reduced_folder in mode_and_band_dir.glob("*.rb"):
        cprint(f"Plotting files of folder {reduced_folder.name}...", "g")
        for fits_file in get_fits_by_tag(reduced_folder, "RAW_INT"):
            plot_fits = Plotter([fits_file],
                                save_path=(mode_and_band_dir / reduced_folder.name))
            plot_fits.add_cphases().add_vis().plot(save=True)
    cprint(f"Finished reducing {band} in {mode}-mode", "lp")
    cprint(f"{'':-^50}", "lp")


def reduce_mode_and_band(raw_dir: Path, calib_dir: Path,
                         product_dir: Path, mode: bool,
                         band: str, tpl_start: str, overwrite: bool) -> None:
    """Reduces either the L- and/or the N-band data for either the 'coherent' and/or
    'incoherent' setting for a single iteration/epoch.

    Notes
    -----
    Removes the old (.sof)-files to ensure proper reduction and then creates folders in
    the 'res_dir'-directory. After this, it starts the reduction with the specified
    settings

    Parameters
    ----------
    raw_dir: Path
        The direcotry containing the raw observation files
    calib_dir: Path
        The directory containing to the observation associated calibration files
    product_dir: Path
        The directory to contain the reduced files
    mode: str
        The mode in which the reduction is to be executed. Either 'coherent',
        'incoherent' or 'both'
    band: str
        The band in which the reduction is to be executed. Either 'lband',
        'nband' or 'both'
    tpl_star: str
        The starting time of observations
    overwrite: bool, optional
        If 'True' overwrites present files from previous reduction
    """
    skip_L, skip_N = True if band == "nband" else False,\
            True if band == "lband" else False
    param_L, param_N = set_script_arguments(mode)
    spectral_binning = get_spectral_binning(raw_dir, tpl_start)
    prepare_catalogs(raw_dir, calib_dir, tpl_start)
    mat_autoPipeline(dirRaw=str(raw_dir), dirResult=str(product_dir),
                     dirCalib=str(calib_dir), tplstartsel=tpl_start,
                     nbCore=6, resol='', paramL=param_L, paramN=param_N,
                     overwrite=int(overwrite), maxIter=1, skipL=int(skip_L),
                     skipN=int(skip_N), spectralBinning=spectral_binning)
    cleanup_reduction(product_dir, mode, band, overwrite)


@print_execution_time
def reduce(raw_dir: Path, product_dir: Path, mode: Optional[str] = "both",
           band: Optional[str] = "both", overwrite: Optional[bool] = False) -> None:
    """Runs the pipeline for the data reduction

    Parameters
    ----------
    raw_dir: Path
        The directory containing the raw observation files
    product_dir: Path
        The directory to contain the reduced files
    mode: str, optional
        The mode in which the reduction is to be executed. Either 'coherent',
        'incoherent' or 'both'
    band: str, optional
        The band in which the reduction is to be executed. Either 'lband',
        'nband' or 'both'
    overwrite: bool, optional
        If 'True' overwrites present files from previous reduction

    Notes
    -----
    The reduction is executed on 6 cores in multiprocessing
    """
    raw_dir = Path(raw_dir).resolve()
    product_dir = Path(product_dir / "reduced").resolve()
    calib_dir = raw_dir / "calib_files"
    modes, bands = get_execution_modes(mode, band)

    prepare_reduction(raw_dir, calib_dir, product_dir, overwrite)
    for tpl_start in sorted(list(get_tpl_starts(raw_dir))):
        cprint(f"{'':-^50}", "lg")
        cprint(f"Reducing data of tpl_start: {tpl_start}", "lp")
        for mode in modes:
            cprint(f"Processing the {mode} mode...", "lp")
            cprint(f"{'':-^50}", "lg")
            for band in bands:
                cprint(f"Processing the {band.title()}...", "lp")
                reduce_mode_and_band(raw_dir, calib_dir, product_dir,
                                     mode, band, tpl_start, overwrite)
    cprint(f"Finished reducing {', '.join(bands)} for {', '.join(modes)}-mode(s)", "lp")