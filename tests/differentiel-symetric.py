from madcad import *
from madcad.gear import *

def sbevelgear(step, z, pitch_cone_angle, **kwargs):
	part = bevelgear(step, z, pitch_cone_angle, **kwargs)
	top = project(part.group(4).barycenter(), Z)
	bot = project(part.group(1).barycenter(), Z)
	return Solid(
		part = part .option(color=gear_color),
		summit = O,
		axis = Axis(top, -Z, interval=(0, length(top))),
		bot = Axis(bot, Z, interval=(0, length(top-bot))),
		)

def bolt(a, b, dscrew, washera=False, washerb=False):
	dir = normalize(b-a)
	rwasher = washer(dscrew)
	thickness = rwasher['part'].box().width.z
	rscrew = screw(dscrew, stceil(distance(a,b) + 1.2*dscrew, precision=0.2))
	rnut = nut(dscrew)
	rscrew['annotations'] = [
				note_distance(O, -stceil(distance(a,b) + 1.2*dscrew)*Z, offset=2*dscrew*X),
				note_radius(rscrew['part'].group(0)),
				]
	return Solid(
			screw = rscrew.place((Pivot, rscrew['axis'], Axis(a-thickness*dir, -dir))), 
			nut = rnut.place((Pivot, rnut['top'], Axis(b+thickness*dir, -dir))),
			w1 = rwasher.place((Pivot, rwasher['top'], Axis(b, -dir))),
			w2 = rwasher.place((Pivot, rwasher['top'], Axis(a, dir))),
			)

settings.primitives['curve_resolution'] = ('rad', 0.105)
#settings.primitives['curve_resolution'] = ('rad', 0.19456)
settings.primitives['curve_resolution'] = ('sqradm', 0.5)


transmiter_angle = pi/6
transmiter_z = 8
gear_step = 6
output_radius = 5
gear_color = vec3(0.2, 0.3, 0.4)
dscrew = 3
neighscrew = 1.3*dscrew
shell_thickness = 1

axis_z = round(transmiter_z/tan(transmiter_angle))
transmiter_rint = stceil((transmiter_z * gear_step / (2*pi) - 0.6*gear_step) * (0.5 + 0.2*sin(transmiter_angle)))

space_radius = transmiter_z*gear_step/(2*pi) / sin(transmiter_angle) * 1.05

#bearing_height = stceil(output_radius)
#bearing_radius = stceil(output_radius*2.5)
#bearing_bore = stceil(output_radius*1.5*2)
bearing_height = 5
bearing_radius = 24/2
bearing_bore = 15/2
out_gear = sbevelgear(gear_step, axis_z, pi/2-transmiter_angle, 
				bore_radius=output_radius, 
				bore_height=1.2*bearing_height,
				)
output = Solid(
	gear = out_gear,
	bearing = bearing(bearing_bore*2, bearing_radius*2, bearing_height)
				.transform(out_gear['axis'].origin - 0.5*bearing_height*Z),
	)
bearing_support = revolution(2*pi, Axis(O,Z), wire([
		out_gear['part'].group(4).barycenter() - bearing_height*Z + output_radius*1.5*0.9*X,
		out_gear['part'].group(4).barycenter() - bearing_height*Z + output_radius*1.5*1.2*X,
		out_gear['part'].group(7).barycenter() + output_radius*1.5*1.2*X - output_radius*0.01*Z,
		]))
out_gear['part'] = union(out_gear['part'], bearing_support).option(color=out_gear['part'].options['color'])
#out_gear['annotations'] = [note_distance(O, out_gear['part'].group(4).barycenter(), offset=20*X)]
#out_gear['annotations'] += [note_distance(O, out_gear['part'].group(7).barycenter(), offset=16*X)]

output1 = output
output2 = deepcopy(output).transform(rotate(pi,Y))

transmiter_axis_thickness = stceil(transmiter_rint*0.2)
transmiter_washer_thickness = stceil(transmiter_rint*0.2)
transmiter_gear = sbevelgear(gear_step, transmiter_z, transmiter_angle, 
				bore_height=0, 
				bore_radius=transmiter_rint,
				)
transmiter = Solid(
		gear = transmiter_gear,
		bearing = slidebearing(
				(transmiter_rint-transmiter_axis_thickness)*2, 
				stfloor(space_radius + dscrew + neighscrew*0.8 - length(transmiter_gear['bot'].origin)), 
				transmiter_axis_thickness,
				) .transform(translate(transmiter_gear['bot'].origin) * rotate(pi,X)),
		washer = washer(
				stceil(transmiter_rint*2), 
				stceil(transmiter_rint*1.8*2), 
				transmiter_washer_thickness,
				) .transform(transmiter_gear['axis'].origin),
		).transform(rotate(pi/2,Y))

transmiter_amount = ceil(axis_z / (1.5*transmiter_z/pi))
transmiters = [deepcopy(transmiter).transform(rotate(i*2*pi/transmiter_amount,Z))  for i in range(transmiter_amount)]

interior_top = revolution(2*pi, Axis(O,Z), Wire([
	out_gear['axis'].origin + bearing_radius*X - bearing_radius*0.15*X,
	out_gear['axis'].origin + bearing_radius*X,
	out_gear['axis'].origin + bearing_radius*X - bearing_height*Z,
	out_gear['axis'].origin + bearing_radius*X - bearing_height*1.2*Z + bearing_height*0.2*X,
	out_gear['axis'].origin + space_radius*X  - bearing_height*1.2*Z,
	]).flip().segmented())
interior_out = (
			interior_top 
			+ interior_top.transform(scaledir(Z,-1)).flip()
			).finish()

r = length(transmiter['gear']['axis'].origin)
h = transmiter_rint
w = r + transmiter_washer_thickness*1.5
interior_transmision = revolution(2*pi, Axis(O,X), Wire([
	2*r*X + h*Z,
	w*X + h*Z,
	w*X + 2.5*h*Z,
	w*X + 2.5*h*Z + h*(X+Z),
	]).flip().segmented())
interior_transmisions = repeat(interior_transmision, transmiter_amount, rotate(2*pi/transmiter_amount, Z))

interior_space = union(
				icosphere(O, space_radius),
				cylinder(out_gear['axis'].origin, out_gear['axis'].origin*vec3(1,1,-1), bearing_radius*1.05, fill=False),
				).flip()

interior_shell = union(interior_space, interior_out)
interior = union(interior_shell, interior_transmisions.group({0,1})) + interior_transmisions.group({2,3,4,5})

# symetrical exterior
exterior_shell = inflate(interior_shell.flip(), shell_thickness)

rscrew = max(bearing_radius + 1.2*neighscrew,  space_radius + dscrew*0.5 + shell_thickness*0.5)
a = 2*dscrew*Z + space_radius*X  + dscrew*X
b = a*vec3(1,1,-1)
bolt = bolt(a, b, dscrew)
bolts = [bolt.transform(rotate((i+0.5)*2*pi/8, Z))  for i in range(8)]

screw_support = web([
	project(a, Z) + dscrew*X,
	a + neighscrew*X,
	b + neighscrew*X,
	project(b, Z) + dscrew*X,
	]).segmented()
screw_supports = revolution(2*pi, Axis(O,Z), screw_support)

exterior_shape = union(exterior_shell, screw_supports)

hole = cylinder(a+1*Z, a*vec3(1,1,-1)-1*Z, dscrew*0.55).flip()
holes = mesh.mesh([hole.transform(b.pose)  for b in bolts])
exterior = intersection(exterior_shape, holes)
sep = square(Axis(1.5*transmiter_rint*Z, Z), space_radius*4)
interior.mergeclose()

interior = interior + extrusion(shell_thickness*Z, interior.frontiers(5,None)).orient().flip()
interior.mergeclose()

part = intersection(exterior, interior).finish()
part_mid = intersection(part, sep + sep.flip().transform(mat3(1,1,-1))) .finish()
part_top = intersection(part, sep.flip()) .finish()
part_bot = part_top.flip().transform(mat3(1,1,-1))

# annotations
transmiters[0]['bearing']['annotations'] = [
	note_radius(transmiter['bearing']['part'].group(1)),
	note_distance_planes(*transmiter['bearing']['part'].group(2).islands()),
	]
output1['bearing']['annotations'] = [
	note_radius(output1['bearing']['part'].group(2)),
	note_radius(output1['bearing']['part'].group(9)),
	note_distance_planes(output1['bearing']['part'].group(0), output1['bearing']['part'].group(3)),
	]

option1 = (sbevelgear(10, 24, radians(70), helix_angle=radians(20), bore_height=0, bore_radius=bearing_radius)
			.transform(translate(5*Z) * rotate(pi,X)))
top_stuff = Solid(part=part_top).transform(30*Z)


def sbevelgear(step, z, pitch_cone_angle, **kwargs):
	part = helical_bevel_gear(step, z, pitch_cone_angle, **kwargs)
	top = project(part.group(4).barycenter(), Z)
	bot = project(part.group(1).barycenter(), Z)
	return Solid(
		part = part .option(color=gear_color),
		summit = O,
		axis = Axis(top, -Z, interval=(0, length(top))),
		bot = Axis(bot, Z, interval=(0, length(top-bot))),
		)

option2 = (sbevelgear(8, 20, radians(70),  helix_angle=radians(20), bore_radius=bearing_radius, bore_height=0, resolution=('sqradm', 0.5))
			.transform(translate(50*Z) * rotate(pi,X)))

option3 = Solid(part=gear(8, 22, 10, helix_angle=radians(20), bore_radius=space_radius, hub_height=0)).transform(-8*Z)
