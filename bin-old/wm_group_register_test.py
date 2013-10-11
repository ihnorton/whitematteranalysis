#!/usr/bin/env python

print "LAUREN should mean rotation be 0?"

import os

import whitematteranalysis as wma
import vtk
import numpy
print 'Read and preprocess'

minimum_length = 60

outdir = os.path.join('.', 'group_register_test')
os.mkdir(outdir)

#number_of_fibers = 1000
number_of_fibers = 300
import multiprocessing
number_of_jobs = multiprocessing.cpu_count()
print 'CPUs detected:', number_of_jobs
#number_of_jobs = 12

pd = wma.io.read_polydata('/Users/lauren/Data/TBI/Tracts/01030-dwi-filt-Ed-DTI-tract.vtp')
pd2 = wma.filter.preprocess(pd, minimum_length)
pd2 = wma.filter.downsample(pd2, number_of_fibers)
pdA = wma.filter.mask(pd2, numpy.ones(number_of_fibers), numpy.ones(number_of_fibers))

pd = wma.io.read_polydata('/Users/lauren/Data/TBI/Tracts/01035-dwi-filt-Ed-DTI-tract.vtp')
pd2 = wma.filter.preprocess(pd, minimum_length)
pd2 = wma.filter.downsample(pd2, number_of_fibers)
pdB = wma.filter.mask(pd2, numpy.ones(number_of_fibers), numpy.multiply(numpy.ones(number_of_fibers), 2))

pd = wma.io.read_polydata('/Users/lauren/Data/TBI/Tracts/01047-dwi-filt-Ed-DTI-tract.vtp')
pd2 = wma.filter.preprocess(pd, minimum_length)
pd2 = wma.filter.downsample(pd2, number_of_fibers)
pdC = wma.filter.mask(pd2, numpy.ones(number_of_fibers), numpy.multiply(numpy.ones(number_of_fibers), 2))

pd = wma.io.read_polydata('/Users/lauren/Data/TBI/Tracts/01053-dwi-filt-Ed-DTI-tract.vtp')
pd2 = wma.filter.preprocess(pd, minimum_length)
pd2 = wma.filter.downsample(pd2, number_of_fibers)
pdD = wma.filter.mask(pd2, numpy.ones(number_of_fibers), numpy.multiply(numpy.ones(number_of_fibers), 2))

pd = wma.io.read_polydata('/Users/lauren/Data/TBI/Tracts/01135-dwi-filt-Ed-DTI-tract.vtp')
pd2 = wma.filter.preprocess(pd, minimum_length)
pd2 = wma.filter.downsample(pd2, number_of_fibers)
pdE = wma.filter.mask(pd2, numpy.ones(number_of_fibers), numpy.multiply(numpy.ones(number_of_fibers), 2))

input_pds = [pdA, pdB, pdC, pdD, pdE]

def view_polydatas(polydata_list):
    appender = vtk.vtkAppendPolyData()
    idx = 0
    for pd in polydata_list:
        nf = pd.GetNumberOfLines()
        print idx
        print nf
        mask = numpy.ones(nf)
        colors = numpy.multiply(mask, idx-1)
        pd2 = wma.filter.mask(pd, mask, colors)
        appender.AddInput(pd2)
        idx = idx + 1
    appender.Update()
    pd3 = appender.GetOutput()
    ren = wma.render.render(pd3)
    return ren

def transform_polydatas(input_pds, register):
    transforms = register.convert_transforms_to_vtk()
    idx = 0
    output_pds = list()
    for transform in transforms:
        transformer = vtk.vtkTransformPolyDataFilter()
        transformer.SetInput(input_pds[idx])
        transformer.SetTransform(transform)
        transformer.Update()
        pd = transformer.GetOutput()
        output_pds.append(pd)
        idx = idx + 1
    return output_pds

register = wma.congeal.CongealTractography()
register.parallelJobs = number_of_jobs
register.parallelJobs = 10
#register.threshold = 5
register.threshold = 0
register.sigma = 10
register.points_per_fiber = 5
#register.sigma = 5
register.fiber_sample_size = 50
#register.fiber_sample_size = 100

# inputs are fixed, moving
for pd in input_pds:
    register.add_subject(pd)

model_pds=list()
for subj in register._subjects:
    model_pds.append(subj._original_fibers.convert_to_polydata())

#ren = view_polydatas(model_pds)

# RUN registration (initial)
register.translate_only()
#register.maxfun = 50
register.maxfun = 100
register.compute()

# RUN registration (initial)
register.rotate_only()
#register.maxfun = 50
register.compute()

# narrower rho parameters, solution should move less
inc_rot = (3.0 / 180.0) * numpy.pi
inc_trans = 5.0
inc_scale = .2 
register.set_rhobeg(inc_rot, inc_trans, inc_scale)
inc_rot = (1.0 / 180.0) * numpy.pi
inc_trans = 2.0
inc_scale = .01
register.set_rhoend(inc_rot, inc_trans, inc_scale)

# RUN registration (second)
register.translate_only()
#register.maxfun = 50
register.maxfun = 100
register.compute()

register.rotate_only()
#register.maxfun = 50
register.compute()

#register.fiber_sample_size = 200
#register.maxfun = 50
#register.compute()

#register.translate_and_rotate()
#register.compute()


# view input data
#ren = view_polydatas(input_pds)

# view output data
output_pds = transform_polydatas(input_pds, register)
ren = view_polydatas(output_pds)

outdir_subdir = os.path.join(outdir, 'out1')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)

model_output_pds=list()
for subj in register._subjects:
    model_output_pds.append(subj._moving_fibers.convert_to_polydata())

ren = view_polydatas(model_output_pds)


# test clustering the data
appender = vtk.vtkAppendPolyData()
for pd in output_pds:
    appender.AddInput(pd)

appender.Update()
pd_all_registered = appender.GetOutput()


pd_c, clusters, colors, embed, distortion = wma.cluster.spectral(pd_all_registered,number_of_jobs=number_of_jobs)

ren = wma.render.render(pd_c)

outdir_subdir = os.path.join(outdir, 'cluster1')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)


# test finer reg
# narrower rho parameters, solution should move less
inc_rot = (1.0 / 180.0) * numpy.pi
inc_trans = 2.0
inc_scale = .05 
register.set_rhobeg(inc_rot, inc_trans, inc_scale)
inc_rot = (.5 / 180.0) * numpy.pi
inc_trans = .5
inc_scale = .01
register.set_rhoend(inc_rot, inc_trans, inc_scale)

#register.fiber_sample_size = 200
register.fiber_sample_size = 100
register.translate_only()
#register.maxfun = 50
register.maxfun = 150
register.compute()

register.rotate_only()
#register.maxfun = 50
register.compute()


# view output data
output_pds = transform_polydatas(input_pds, register)
ren = view_polydatas(output_pds)

outdir_subdir = os.path.join(outdir, 'out2')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)

# test clustering the data
appender = vtk.vtkAppendPolyData()
for pd in output_pds:
    appender.AddInput(pd)

appender.Update()
pd_all_registered = appender.GetOutput()


pd_c, clusters, colors, embed, distortion = wma.cluster.spectral(pd_all_registered,number_of_jobs=number_of_jobs)

ren = wma.render.render(pd_c)

outdir_subdir = os.path.join(outdir, 'cluster2')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)

# test another round!
#register.fiber_sample_size = 300
register.fiber_sample_size = 150
register.translate_only()
register.maxfun = 150
register.compute()

register.rotate_only()
#register.maxfun = 50
register.compute()


# view output data
output_pds = transform_polydatas(input_pds, register)
ren = view_polydatas(output_pds)

outdir_subdir = os.path.join(outdir, 'out3')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)

# test more...
inc_rot = (1 / 180.0) * numpy.pi
inc_trans = 1.0
inc_scale = .05 
register.set_rhobeg(inc_rot, inc_trans, inc_scale)
inc_rot = (.5 / 180.0) * numpy.pi
inc_trans = .5
inc_scale = .01
register.set_rhoend(inc_rot, inc_trans, inc_scale)

register.translate_and_rotate_and_scale()
register.maxfun = 200
register.compute()

# view output data
output_pds = transform_polydatas(input_pds, register)
ren = view_polydatas(output_pds)

outdir_subdir = os.path.join(outdir, 'out_converge')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)


# test clustering the data
appender = vtk.vtkAppendPolyData()
for pd in output_pds:
    appender.AddInput(pd)

appender.Update()
pd_all_registered = appender.GetOutput()


pd_c, clusters, colors, embed, distortion = wma.cluster.spectral(pd_all_registered,number_of_jobs=number_of_jobs)

ren = wma.render.render(pd_c)

outdir_subdir = os.path.join(outdir, 'cluster_converge')
os.mkdir(outdir_subdir)
ren.save_views(outdir_subdir)


for subj in register._subjects:
    print subj.transform






