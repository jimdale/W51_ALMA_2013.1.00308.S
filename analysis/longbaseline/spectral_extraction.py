import numpy as np
from astropy import units as u
import pyregion
import radio_beam
from spectral_cube import SpectralCube
import paths
from astropy.io import fits
from astropy import wcs

tmplt = '{reg}cax.SPW{0}_ALL.image.fits'

#region_list = pyregion.open("cores_longbaseline_spectralextractionregions.reg")
#region_list += pyregion.open("e2e_se_jet.reg")
#region_list += pyregion.open("e2w_nitrogenic_bubble.reg")
#region_list = pyregion.open("cores_longbaseline_spectralextractionregions_pix.reg")
#fh = fits.open('W51e2cax.cont.image.pbcor.fits')
#mywcs = wcs.WCS(fh[0].header)

for region, region_list in (('W51e2', pyregion.open(paths.rpath("cores_longbaseline_spectralextractionregions_pix.reg"))),
                            ('W51n', pyregion.open(paths.rpath("cores_longbaseline_spectralextractionregions_pix_north.reg")))):
    for spw in range(0,10): #(2,4,6):
        try:
            cube = SpectralCube.read(tmplt.format(spw, reg=region))
        except IOError:
            print("didn't find {0}".format(tmplt.format(spw, reg=region)))
            continue
        print(cube)
        try:
            beam = radio_beam.Beam.from_fits_header(cube.header)
        except TypeError:
            if hasattr(cube, 'beams'):
                beam = radio_beam.Beam(major=np.nanmedian([bm.major.to(u.deg).value for bm in cube.beams]),
                                       minor=np.nanmedian([bm.minor.to(u.deg).value for bm in cube.beams]),
                                       pa=np.nanmedian([bm.pa.to(u.deg).value for bm in cube.beams]),
                                      )
            else:
                beam = None

        for reg in region_list:
            if 'text' not in reg.attr[1]:
                continue
            name = reg.attr[1]['text']
            if name:
                print("Extracting {0} from {1} with region {2}".format(name, spw, reg))
                SL = pyregion.ShapeList([reg])
                try:
                    sc = cube.subcube_from_ds9region(SL)
                except ValueError as ex:
                    print(ex)
                    continue
                print("Done subcubing {0} from {1} with region {2}".format(name, spw, reg))
                spec = sc.mean(axis=(1,2))
                assert not all(np.isnan(spec))

                if beam is not None:
                    spec.meta['beam'] = beam
                spec.hdu.writeto(paths.dpath("longbaseline/spectra/{0}_{reg}_spw{1}_mean.fits".format(name, spw, reg=region)),
                                 clobber=True)
