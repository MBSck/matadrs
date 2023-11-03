"""Created on Apr 11 2019

@author: fmillour
"""
import os
from pathlib import Path
from typing import Optional
from shutil import copyfile

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits


def calib_BCD(iifile: Path, iofile: Path,
              oifile: Path, oofile: Path,
              outputfile: Optional[Path] = os.getenv("HOME") + "/toto.fits",
              lim: Optional[int] = 180,
              plot: Optional[bool] = True) -> None:
    """Executes the BCD-calibration.

    Parameters
    ----------
    iifile : pathlib.Path
        BCD In-In file.
    iofile : pathlib.Path
        BCD In-Out file.
    oifile : pathlib.Path
        BCD Out-In file.
    oofile : pathlib.Path
        BCD Out-Out file.
    outputfile : pathlib.Path, optional
        Path to the output file.
    lim : int, optional
    plot : int, optional
    """
    copyfile(iifile, outputfile)
    outhdul = fits.open(outputfile, mode="update")

    dinin = fits.open(iifile)
    doutout = fits.open(oofile)

    iit3p = dinin["OI_T3"].data["T3PHI"] * np.pi / 180.0
    oot3p = doutout["OI_T3"].data["T3PHI"] * np.pi / 180.0

    iidp = dinin["OI_VIS"].data["VISPHI"] * np.pi / 180.0
    oodp = doutout["OI_VIS"].data["VISPHI"] * np.pi / 180.0

    iiva = dinin["OI_VIS"].data["VISAMP"]
    oova = doutout["OI_VIS"].data["VISAMP"]

    iiv2 = dinin["OI_VIS2"].data["VIS2DATA"]
    oov2 = doutout["OI_VIS2"].data["VIS2DATA"]

    if os.path.exists(iofile):
        dinout = fits.open(iofile)
        iot3p = dinout["OI_T3"].data["T3PHI"] * np.pi / 180.0
        iodp = dinout["OI_VIS"].data["VISPHI"] * np.pi / 180.0
        iova = dinout["OI_VIS"].data["VISAMP"]
        iov2 = dinout["OI_VIS2"].data["VIS2DATA"]
    else:
        iot3p = 0.0 * iit3p
        iodp = 0.0 * iidp
        iova = 0.0 * iiva
        iov2 = 0.0 * iiv2
    if os.path.exists(oifile):
        doutin = fits.open(oifile)
        oit3p = doutin["OI_T3"].data["T3PHI"] * np.pi / 180.0
        oidp = doutin["OI_VIS"].data["VISPHI"] * np.pi / 180.0
        oiva = doutin["OI_VIS"].data["VISAMP"]
        oiv2 = doutin["OI_VIS2"].data["VIS2DATA"]
    else:
        oit3p = 0.0 * iit3p
        oidp = 0.0 * iidp
        oiva = 0.0 * iiva
        oiv2 = 0.0 * iiv2

    sin_iidp = np.sin(iidp)
    sin_iit3p = np.sin(iit3p)
    sin_iodp = np.sin(iodp)
    sin_iot3p = np.sin(iot3p)
    sin_oidp = np.sin(oidp)
    sin_oit3p = np.sin(oit3p)
    sin_oodp = np.sin(oodp)
    sin_oot3p = np.sin(oot3p)
    cos_iidp = np.cos(iidp)
    cos_iit3p = np.cos(iit3p)
    cos_iodp = np.cos(iodp)
    cos_iot3p = np.cos(iot3p)
    cos_oidp = np.cos(oidp)
    cos_oit3p = np.cos(oit3p)
    cos_oodp = np.cos(oodp)
    cos_oot3p = np.cos(oot3p)

    iitwl = dinin["OI_WAVELENGTH"].data["EFF_WAVE"]

    # is_flux = True
    # try:
    #     iifl =   dinin['OI_FLUX'].data['FLUXDATA'];
    #     iofl =  dinout['OI_FLUX'].data['FLUXDATA'];
    #     oifl =  doutin['OI_FLUX'].data['FLUXDATA'];
    #     oofl = doutout['OI_FLUX'].data['FLUXDATA'];
    # except KeyError as e:
    #     print(e)
    #     is_flux = False
    #     iifl = np.nan*iiv2
    #     iofl = np.nan*iiv2
    #     oifl = np.nan*iiv2
    #     oofl = np.nan*iiv2

    nwlen = np.shape(iit3p)[1]

    # NOTE: Add the different exposures up
    nrepeatii = int(np.shape(iit3p)[0] / 4)
    # print(nrepeatii)
    nrepeatii = int(np.shape(iiv2)[0] / 6)
    nrepeatoo = int(np.shape(oov2)[0] / 6)
    if os.path.exists(oifile):
        nrepeatoi = int(np.shape(oiv2)[0] / 6)
    else:
        nrepeatoi = 0
    if os.path.exists(iofile):
        nrepeatio = int(np.shape(iov2)[0] / 6)
    else:
        nrepeatio = 0

    # print(nrepeatii,nrepeatoo,nrepeatio,nrepeatoi)
    # print(nrepeatii)
    # print(nrepeatio)
    # print(nrepeatoi)
    # print(nrepeatoo)

    # NOTE: Store multiple exposures data into the first 6 rows
    if nrepeatii > 1:
        for i in np.arange(nrepeatii - 1):
            for j in np.arange(6):
                iiva[j, :] += iiva[(i + 1) * 6 + j, :]
                iiv2[j, :] += iiv2[(i + 1) * 6 + j, :]
                # iidp[j,:] += iidp[(i+1)*6+j,:]
                sin_iidp[j, :] += sin_iidp[(i + 1) * 6 + j, :]
                cos_iidp[j, :] += cos_iidp[(i + 1) * 6 + j, :]
            for j in np.arange(4):
                # iit3p[j,:] += iit3p[(i+1)*4+j,:]
                sin_iit3p[j, :] += sin_iit3p[(i + 1) * 4 + j, :]
                cos_iit3p[j, :] += cos_iit3p[(i + 1) * 4 + j, :]

    if nrepeatio > 1:
        for i in np.arange(nrepeatio - 1):
            for j in np.arange(6):
                iova[j, :] += iova[(i + 1) * 6 + j, :]
                iov2[j, :] += iov2[(i + 1) * 6 + j, :]
                # iodp[j,:] += iodp[(i+1)*6+j,:]
                sin_iodp[j, :] += sin_iodp[(i + 1) * 6 + j, :]
                cos_iodp[j, :] += cos_iodp[(i + 1) * 6 + j, :]
            for j in np.arange(4):
                # iot3p[j,:] += iot3p[(i+1)*4+j,:]
                sin_iot3p[j, :] += sin_iot3p[(i + 1) * 4 + j, :]
                cos_iot3p[j, :] += cos_iot3p[(i + 1) * 4 + j, :]

    if nrepeatoi > 1:
        for i in np.arange(nrepeatoi - 1):
            for j in np.arange(6):
                oiva[j, :] += oiva[(i + 1) * 6 + j, :]
                oiv2[j, :] += oiv2[(i + 1) * 6 + j, :]
                # oidp[j,:] += oidp[(i+1)*6+j,:]
                sin_oidp[j, :] += sin_oidp[(i + 1) * 6 + j, :]
                cos_oidp[j, :] += cos_oidp[(i + 1) * 6 + j, :]
            for j in np.arange(4):
                # oit3p[j,:] += oit3p[(i+1)*4+j,:]
                sin_oit3p[j, :] += sin_oit3p[(i + 1) * 4 + j, :]
                cos_oit3p[j, :] += cos_oit3p[(i + 1) * 4 + j, :]

    if nrepeatoo > 1:
        for i in np.arange(nrepeatoo - 1):
            for j in np.arange(6):
                oova[j, :] += oova[(i + 1) * 6 + j, :]
                oov2[j, :] += oov2[(i + 1) * 6 + j, :]
                # oodp[j,:] += oodp[(i+1)*6+j,:]
                sin_oodp[j, :] += sin_oodp[(i + 1) * 6 + j, :]
                cos_oodp[j, :] += cos_oodp[(i + 1) * 6 + j, :]
            for j in np.arange(4):
                # oot3p[j,:] += oot3p[(i+1)*4+j,:]
                sin_oot3p[j, :] += sin_oot3p[(i + 1) * 4 + j, :]
                cos_oot3p[j, :] += cos_oot3p[(i + 1) * 4 + j, :]
                # oofl[j, :] += oofl[(i + 1) * 4 + j, :]

    # NOTE: Treat closure phases
    idx = np.array([[0, 0, 3, 3], [1, 2, 1, 2], [2, 1, 2, 1], [3, 3, 0, 0]])
    sign = np.array([[1, -1, 1, -1], [1, 1, -1, -1], [1, 1, -1, -1], [1, -1, 1, -1]])

    # NOTE: Initialize closure phase with same shape as input
    sin_avg = np.zeros((4, nwlen))
    cos_avg = np.zeros((4, nwlen))
    closfinal = np.zeros((4, nwlen))
    if plot:
        plt.figure(51)

    for i in np.arange(4):
        # ix=20
        # print(iit3p[idx[i,0],ix]*180.0/np.pi,oit3p[idx[i,0],ix]*180.0/np.pi,iot3p[idx[i,0],ix]*180.0/np.pi,oot3p[idx[i,0],ix]*180.0/np.pi)
        # closfinal[i,:] = (sign[i,0] * iit3p[idx[i,0],:] + sign[i,1] * oit3p[idx[i,1],:] +\
        #                   sign[i,2] * iot3p[idx[i,2],:] + sign[i,3] * oot3p[idx[i,3],:])/\
        #                   (nrepeatii+nrepeatoi+nrepeatio+nrepeatoo)
        sin_avg[i, :] = (
            sign[i, 0] * sin_iit3p[idx[i, 0], :]
            + sign[i, 1] * sin_oit3p[idx[i, 1], :]
            + sign[i, 2] * sin_iot3p[idx[i, 2], :]
            + sign[i, 3] * sin_oot3p[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        cos_avg[i, :] = (
            1.0 * cos_iit3p[idx[i, 0], :]
            + 1.0 * cos_oit3p[idx[i, 1], :]
            + 1.0 * cos_iot3p[idx[i, 2], :]
            + 1.0 * cos_oot3p[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        closfinal[i, :] = np.arctan2(sin_avg[i, :], cos_avg[i, :]) * 180.0 / np.pi
        if plot:
            plt.subplot(2, 2, i + 1)
            plt.plot(iitwl * 1e6, iit3p[i, :], label="II")
            plt.plot(iitwl * 1e6, oot3p[i, :], label="OO")
            plt.plot(iitwl * 1e6, iot3p[i, :], label="IO")
            plt.plot(iitwl * 1e6, oit3p[i, :], label="OI")
            plt.plot(iitwl * 1e6, closfinal[i, :])
            plt.ylabel("Closure phase")
            plt.legend()
            plt.ylim(-lim, lim)

    # NOTE: Treat differential phases
    idx = np.array([[0, 0, 0, 0],
                    [1, 1, 1, 1],
                    [2, 3, 4, 5],
                    [3, 2, 5, 4],
                    [4, 5, 2, 3],
                    [5, 4, 3, 2]])
    sign = np.array([[1, -1, 1, -1],
                     [1, 1, -1, -1],
                     [1, 1, 1, 1],
                     [1, 1, 1, 1],
                     [1, 1, 1, 1],
                     [1, 1, 1, 1],])

    sin_avg = np.zeros((6, nwlen))
    cos_avg = np.zeros((6, nwlen))
    dpfinal = np.zeros((6, nwlen))
    if plot:
        plt.figure(52)
    # print(np.shape(idx))
    for i in np.arange(6):
        # dpfinal[i,:] = (sign[i,0] * iidp[idx[i,0],:] + sign[i,1] * oidp[idx[i,1],:] +\
        #                 sign[i,2] * iodp[idx[i,2],:] + sign[i,3] * oodp[idx[i,3],:])/\
        #                 (nrepeatii+nrepeatoi+nrepeatio+nrepeatoo)
        sin_avg[i, :] = (
            sign[i, 0] * sin_iidp[idx[i, 0], :]
            + sign[i, 1] * sin_oidp[idx[i, 1], :]
            + sign[i, 2] * sin_iodp[idx[i, 2], :]
            + sign[i, 3] * sin_oodp[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        cos_avg[i, :] = (
            1.0 * cos_iidp[idx[i, 0], :]
            + 1.0 * cos_oidp[idx[i, 1], :]
            + 1.0 * cos_iodp[idx[i, 2], :]
            + 1.0 * cos_oodp[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        dpfinal[i, :] = np.arctan2(sin_avg[i, :], cos_avg[i, :]) * 180.0 / np.pi
        if plot:
            plt.subplot(3, 2, i + 1)
            plt.plot(iitwl * 1e6, iidp[i, :], label="II")
            plt.plot(iitwl * 1e6, oodp[i, :], label="OO")
            plt.plot(iitwl * 1e6, iodp[i, :], label="IO")
            plt.plot(iitwl * 1e6, oidp[i, :], label="OI")
            plt.plot(iitwl * 1e6, dpfinal[i, :])
            plt.ylim(-lim, lim)
            plt.ylabel("Differential phase")
            plt.legend()

    # NOTE: Treat visamp (or correlated fluxes)
    vafinal = np.zeros((6, nwlen))

    if plot:
        plt.figure(53)
    for i in np.arange(6):
        vafinal[i, :] = (
            iiva[i, :] + oiva[idx[i, 1], :] + iova[idx[i, 2], :] + oova[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        if plot:
            plt.subplot(3, 2, i + 1)
            plt.plot(iitwl * 1e6, iiva[i, :], label="II")
            plt.plot(iitwl * 1e6, oova[i, :], label="OO")
            plt.plot(iitwl * 1e6, iova[i, :], label="IO")
            plt.plot(iitwl * 1e6, oiva[i, :], label="OI")
            plt.plot(iitwl * 1e6, vafinal[i, :])
            plt.ylabel("VISAMP")
            plt.legend()

    # NOTE: Treat visibilities
    v2final = np.zeros((6, nwlen))

    if plot:
        plt.figure(50)
    # print(np.shape(idx))

    for i in np.arange(6):
        v2final[i, :] = (
            iiv2[i, :] + oiv2[idx[i, 1], :] + iov2[idx[i, 2], :] + oov2[idx[i, 3], :]
        ) / (nrepeatii + nrepeatoi + nrepeatio + nrepeatoo)
        if plot:
            plt.subplot(3, 2, i + 1)
            plt.plot(iitwl * 1e6, iiv2[i, :], label="II")
            plt.plot(iitwl * 1e6, oov2[i, :], label="OO")
            plt.plot(iitwl * 1e6, iov2[i, :], label="IO")
            plt.plot(iitwl * 1e6, oiv2[i, :], label="OI")
            plt.plot(iitwl * 1e6, v2final[i, :])
            plt.ylim(0, 1)
            plt.ylabel("Squared visibility")
            plt.legend()

    outhdul["OI_T3"].data = outhdul["OI_T3"].data[0:4]
    outhdul["OI_T3"].data["T3PHI"] = closfinal[0:4]
    outhdul["OI_VIS"].data = outhdul["OI_VIS"].data[0:6]
    outhdul["OI_VIS"].data["VISPHI"] = dpfinal[0:6]
    outhdul["OI_VIS"].data["VISAMP"] = vafinal
    outhdul["OI_VIS2"].data = outhdul["OI_VIS2"].data[0:6]
    outhdul["OI_VIS2"].data["VIS2DATA"] = v2final
    # if is_flux:
    #     outhdu['OI_FLUX'].data = outhdu['OI_FLUX'].data[0:4]
    #     outhdu['OI_FLUX'].data['FLUXDATA'] = flfinal

    if "correlated" in dinin["OI_VIS"].header["AMPTYP"]:
        outhdul["OI_VIS"].header["AMPTYP"] = "correlated flux"

    del outhdul[0].header["HIERARCH ESO INS BCD1 ID"]
    del outhdul[0].header["HIERARCH ESO INS BCD2 ID"]
    del outhdul[0].header["HIERARCH ESO INS BCD1 NAME"]
    del outhdul[0].header["HIERARCH ESO INS BCD2 NAME"]
    outhdul[0].header["HIERARCH ESO INS BCD1 ID"] = " "
    outhdul[0].header["HIERARCH ESO INS BCD2 ID"] = " "
    outhdul[0].header["HIERARCH ESO INS BCD1 NAME"] = " "
    outhdul[0].header["HIERARCH ESO INS BCD2 NAME"] = " "

    # NOTE: Changes are written back to original.fits
    outhdul.flush()
    outhdul.close()
    dinin.close()
    if os.path.exists(iofile):
        dinout.close()
    if os.path.exists(oifile):
        doutin.close()
    doutout.close()
    # calib_BCD(inin, inout, outin, outout, outputfile=os.getenv("HOME")+"/toto.fits")

    # print(os.getenv("HOME")+"/toto.fits")

    if plot:
        pass
        plt.show()
