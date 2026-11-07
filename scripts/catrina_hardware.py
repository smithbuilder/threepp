"""Original lowrider hardware, using catalog construction as visual guidance.

This is custom game geometry, not manufacturing CAD or an installation design.
Called by catrina_generate after gear/trunk. Fixed steel members are never scaled.
"""
import math
import numpy as np
from scipy.spatial.transform import Rotation


def add_hardware(ctx):
    M, g, parent = ctx['M'], ctx['g'], ctx['parent']
    body, HUB, Z = ctx['body'], ctx['HUB'], ctx['ZAXLE']
    box, cylinder, tube, torus = (ctx[k] for k in ('box', 'cylinder', 'tube', 'torus'))
    chrome, rubber, black = (ctx[k] for k in ('chrome', 'rubber', 'black'))
    coat = M.mat('hardware_black_powdercoat', 0x27292d, .46, 0)
    zinc = M.mat('zinc_plated_fasteners', 0xa5a9ac, .30, .92)
    brass = M.mat('hydraulic_brass_fittings', 0xb19a64, .28, .95)
    shock = M.mat('damper_anodized_alloy', 0x78828a, .29, .88)
    redcoat = M.mat('hydraulic_solenoid_red', 0x6f1437, .35, 0)
    ids = {n['name']: i for i, n in enumerate(M.nodes)}
    # Leave a genuine clearance pocket below the closed hood/deck. The spring
    # cup remains at .55m; only fixed ram tops and their frame saddles move.
    for i in range(4):
        n, barrel, rod = (ids[f'hydraulic_{i}'], ids[f'hydraulic_{i}_barrel'], ids[f'hydraulic_{i}_rod'])
        M.nodes[n]['translation'][1] -= .04
        M.nodes[rod]['translation'][1] += .04
        M.origins[n][1] -= .04
        M.origins[barrel][1] -= .04
        M.joints[f'hydraulic_{i}']['a'][1] = .86
        M.joints[f'hydraulic_{i}'].update(rodLength=.245,barrelLength=.245,
            cupRestDistance=.310,cupTravelMinimum=.280,cupTravelMaximum=.430,
            minimumSpringLength=.114,coilSolidHeight=.102)
    for p in M.parts:
        if p['name'] in ('chassis.ram_tower', 'chassis.ram_mount'):
            p['p'][:, 1] -= .04
    M.parts[:] = [p for p in M.parts if not p['name'].startswith('hydraulic.pressure_hose')]

    def fastener(c, axis=(0, 0, 1), radius=.013, span=.035):
        c, axis = np.array(c, float), np.array(axis, float)
        cylinder('hardware.bolt_shank', c-axis*span/2, c+axis*span/2, radius*.55, zinc, 10)
        for sign in (-1, 1):
            tip = c+axis*span*.5*sign
            cylinder('hardware.hex_head', tip, tip+axis*.008*sign, radius, zinc, 6)

    def eye(c, axis=(0, 0, 1), r=.025):
        c, axis = np.array(c, float), np.array(axis, float)
        torus('hardware.eye_housing', c, r*.78, r*.24, zinc, axis=axis, segments=20, sides=8)
        cylinder('hardware.rubber_eye_bush', c-axis*.016, c+axis*.016, r*.65, rubber, 16)
        fastener(c, axis, .011, .042)

    def strut(a, b, width=.055, depth=.035, name='hardware.boxed_bracket'):
        a, b = np.array(a), np.array(b)
        g.box(name, (a+b)*.5, (width, float(np.linalg.norm(b-a)), depth), coat, .006, B=g.basis(b-a))

    def socket_aim(axis,pin_axis):
        y=-np.asarray(axis,float);z=np.asarray(pin_axis,float)-np.dot(pin_axis,y)*y
        z/=np.linalg.norm(z);x=np.cross(y,z)
        return Rotation.from_matrix(np.c_[x,y,z]).as_quat()

    def fixed_spherical_joint(name,node,c,pin_axis,foot_direction=-1):
        c=np.array(c,float);pin_axis=np.array(pin_axis,float);pin_axis/=np.linalg.norm(pin_axis)
        q=np.r_[np.cross([0,0,1],pin_axis),1+pin_axis[2]];q/=np.linalg.norm(q)
        joint=M.node(name,node,c,rotation=q.tolist(),extras={'fixedPinAxis':pin_axis.tolist(),'bearingMisalignmentLimitDegrees':30})
        with parent(joint):
            rows=[]
            # Spherical inner bearing with a real through bore. Its ball and
            # pin stay on the clevis axis while the outer socket articulates.
            for theta in np.linspace(math.asin(.006/.015),math.pi-math.asin(.006/.015),7):
                rows.append([c+[.015*math.sin(theta)*math.cos(a),.015*math.sin(theta)*math.sin(a),.015*math.cos(theta)]for a in np.linspace(0,math.tau,21)])
            M.grid('damper.spherical_inner_ball',rows,zinc)
            cylinder('damper.fixed_eye_pin',c+[0,0,-.042],c+[0,0,.042],.0055,zinc,12)
            for sign in (-1,1):
                cylinder('damper.high_misalignment_spacer',c+[0,0,sign*.014],c+[0,0,sign*.028],.008,zinc,12,r2=.012)
                cylinder('damper.fixed_pin_head',c+[0,0,sign*.040],c+[0,0,sign*.048],.011,zinc,6)
        with parent(node):
            B=g.basis(pin_axis)
            for sign in (-1,1):
                g.box('damper.pin_clevis',c+pin_axis*sign*.034+B[:,2]*.016*foot_direction,(.060,.010,.064),coat,.004,B=B)
        return joint

    def frame_beam(name,a,b,width=.095,height=.13):
        a,b=np.array(a,float),np.array(b,float)
        axis=(b-a)/np.linalg.norm(b-a)
        across=np.cross(axis,[0,1,0]);across/=np.linalg.norm(across)
        up=np.cross(across,axis)
        g.box(name,(a+b)*.5,(width,float(np.linalg.norm(b-a))+.010,height),coat,.007,B=np.c_[across,axis,up])

    # Real boxed rails have broad planar webs and narrow corner radii. The old
    # four-sided radial tube used smooth normals and read as round pipe.
    M.parts[:]=[p for p in M.parts if not p['name'].startswith('chassis.boxed_X_rail')
                and p['name'] not in ('chassis.body_outrigger','chassis.crossmember')]
    rail=np.array([[.57,.27,2.39],[.57,.27,1.53],[.22,.25,.40],[.12,.25,-.20],[.52,.29,-1.46],[.58,.32,-2.30]])
    with parent(body):
        for s in (-1,1):
            path=rail.copy();path[:,0]*=s
            for a,b in zip(path[:-1],path[1:]):frame_beam('chassis.boxed_X_rail',a,b)
            for p in path[1:-1]:
                box('chassis.junction_gusset',p+[0,.068,0],(.125,.012,.16),coat,.005)
                for dz in (-.05,.05):
                    cylinder('chassis.gusset_plug_weld',p+[0,.074,dz],p+[0,.077,dz],.009,coat,10)
            for z in (-2.17,-.90,.80,2.18):
                x=np.interp(z,rail[::-1,2],rail[::-1,0]);y=np.interp(z,rail[::-1,2],rail[::-1,1])
                frame_beam('chassis.body_outrigger',[s*x,y,z],[s*.89,y,z],.065,.075)
                cylinder('chassis.body_mount_bush',(s*.865,y+.035,z),(s*.865,y+.062,z),.032,rubber,20)
                cylinder('chassis.body_mount_bolt',(s*.865,y+.061,z),(s*.865,y+.072,z),.010,zinc,6)
            frame_beam('chassis.rack_stanchion',[s*.575,.32,-2.23],[s*.575+.008,.600,-2.23],.055,.055)
        for z in (1.98,-.75,-2.23):
            x=np.interp(z,rail[::-1,2],rail[::-1,0]);y=np.interp(z,rail[::-1,2],rail[::-1,1])
            frame_beam('chassis.crossmember',[-x,y,z],[x,y,z],.075,.095)
            for s in (-1,1):
                box('chassis.crossmember_end_plate',(s*x,y,z),(.115,.115,.018),coat,.005)

    # Replace narrow tube silhouettes with pressed-channel wishbone arms.
    # The current presentation solver retains equal-length parallel pivots.
    M.parts[:] = [p for p in M.parts if not p['name'].startswith(('front.control_arm', 'front.pivot_shaft'))]
    for i in range(2):
        s = -1 if i == 0 else 1
        for upper in (False, True):
            name = f'front_{i}_'+('upper' if upper else 'lower')
            a = np.array([s*.18, .43 if upper else .25, Z])
            b = np.array([s*.715, a[1], Z])
            span = .16 if upper else .22
            with parent(ids[name]):
                for dz in (-span, span):
                    inner = a+[0, 0, dz]
                    # A boxed channel with folded edges; original dimensions.
                    strut(inner, b, .060 if upper else .075, .031 if upper else .040)
                    cylinder('front.cross_shaft_bushing', inner+[0, 0, -.032], inner+[0, 0, .032], .029, rubber, 18)
                    for end in (-1, 1):
                        cylinder('front.bush_sleeve', inner+[0, 0, end*.030], inner+[0, 0, end*.039], .032, zinc, 18)
                    fastener(inner, radius=.014, span=.09)
                cylinder('front.cross_shaft', a+[0, 0, -span-.055], a+[0, 0, span+.055], .011, zinc, 14)
                cylinder('front.ball_joint_cap', b+[0, -.018, 0], b+[0, .025, 0], .035, zinc, 20)
                torus('front.ball_joint_boot', b+[0, .005, 0], .028, .008, rubber, axis=(0, 1, 0), segments=20, sides=8)
                if not upper:
                    p = a+(b-a)*.69
                    cylinder('front.spring_load_plate', p+[0, -.012, 0], p+[0, .012, 0], .073, coat, 24)
            with parent(body):
                for dz in (-span, span):
                    # Inboard eyes visibly connect to a welded frame bracket.
                    strut(a+[0, 0, dz], [s*.57, .27, Z+dz], .046, .042)

    for i in range(4):
        s, front = (-1 if i % 2 == 0 else 1), i < 2
        # Custom short-travel ram: the 41.275mm casing and 19.05mm shaft
        # combine catalog examples; neither diameter pair nor casing length
        # is represented as an exact six-inch commercial cylinder SKU.
        hydraulic_top = np.array([s*(.55 if front else .56), .86, Z if front else -Z])
        barrel_node = ids[f'hydraulic_{i}_barrel']
        piston_node = ids[f'hydraulic_{i}_rod']
        M.parts[:] = [p for p in M.parts if not (
            (p['parent'] == barrel_node and p['name'] in ('hydraulic.barrel', 'hydraulic.seal_collar')) or
            (p['parent'] == piston_node and p['name'] == 'hydraulic.piston_rod'))]
        with parent(barrel_node):
            cylinder('hydraulic.barrel', hydraulic_top, hydraulic_top+[0, -.245, 0], .0206375, chrome, 24)
            for dy in (-.015, -.233):
                cylinder('hydraulic.seal_collar', hydraulic_top+[0, dy+.008, 0], hydraulic_top+[0, dy-.008, 0], .025, zinc, 24)
            cylinder('hydraulic.port_fitting', hydraulic_top+[0, -.04, .018], hydraulic_top+[0, -.04, .036], .010, brass, 6)
        M.node(f'hydraulic_{i}_barrel_end',barrel_node,hydraulic_top+[0,-.245,0])
        cup = np.array([hydraulic_top[0], .55, hydraulic_top[2]])
        with parent(piston_node):
            cylinder('hydraulic.piston_rod', cup, cup+[0, .245, 0], .009525, chrome, 20)
        M.node(f'hydraulic_{i}_rod_tip',piston_node,cup+[0,.245,0])
        M.node(f'hydraulic_{i}_cup_top',piston_node,cup+[0,.015,0])
        with parent(body):
            z = hydraulic_top[2]
            tube('hydraulic.pressure_hose', [hydraulic_top+[0,-.04,.036], (s*.46,.65,z+.07), (s*.39,.36,z+.13), (s*.39,.35,-1.90)], .0055, black, 8)
        if front:
            a = np.array([s*.18, .25, Z])
            b = np.array([s*.715, .25, Z])
            lower_node = ids[f'front_{i}_lower']
            bottom = a+(b-a)*.38+[0, .03, .12]
            top = np.array([s*.48, .78, Z+.12])
            barrel_end, rod_length = .39, .36
        else:
            a = np.array([s*.56, .33, -.45])
            b = np.array([s*.56, .33, -Z])
            lower_node = ids[f'rear_{i}_lower']
            bottom = a+(b-a)*.84+[-s*.10, .02, 0]
            top = np.array([s*.20, .50, -2.00])
            barrel_end, rod_length = .665, .660
        d = float(np.linalg.norm(bottom-top))
        axis = (bottom-top)/d
        pin_axis=np.array([0,0,1]if front else[.9,-.25,-s*.35],float);pin_axis/=np.linalg.norm(pin_axis)
        quat=socket_aim(axis,pin_axis)
        n = M.node(f'damper_{i}', body, top, rotation=quat.tolist(), extras={
            'construction': 'separate telescopic damper, fixed barrel and sliding rod',
            'frameEye': top.tolist(), 'movingEye': bottom.tolist(),
            'barrelEnd': barrel_end, 'rodLength': rod_length,
            'mountNode': M.nodes[lower_node]['name'], 'mountMotionRatio': .38 if front else .84,
            'movingEyeInboardOffset': 0 if front else .10})
        with parent(n):
            # Geometry authored along local -Y, with a rest aiming quaternion.
            cylinder('damper.fixed_body', top+[0, -.035, 0], top+[0, -barrel_end, 0], .0254, shock, 24)
            for y in (-.042, -barrel_end+.012):
                cylinder('damper.end_cap', top+[0, y-.007, 0], top+[0, y+.007, 0], .028, zinc, 24)
            cylinder('damper.rod_seal', top+[0, -barrel_end-.004, 0], top+[0, -barrel_end+.004, 0], .012, rubber, 20)
            torus('damper.socket_race',top,.017,.006,zinc,axis=(0,0,1),segments=20,sides=8)
            # A welded neck overlaps the eye race and the upper end cap.
            cylinder('damper.eye_neck',top+[0,-.017,0],top+[0,-.043,0],.010,zinc,12)
        rod_origin = top+[0, -d, 0]
        rod = M.node(f'damper_{i}_rod', n, rod_origin)
        with parent(rod):
            cylinder('damper.polished_piston_rod', rod_origin+[0, .018, 0], rod_origin+[0, rod_length, 0], .0079375, chrome, 18)
            torus('damper.socket_race',rod_origin,.017,.006,zinc,axis=(0,0,1),segments=20,sides=8)
        with parent(body):
            # Open fork-side load paths leave the moving shock in a pocket.
            # A central tower directly below the eye would intersect its body.
            if front:
                for fork in (-1,1):
                    strut([s*.57,.27,top[2]+fork*.065],top+[0,-.030,fork*.045],.024,.024,'damper.support_web')
            else:
                B=g.basis(pin_axis)
                base=np.array([s*.20,.31,top[2]-.070])
                for fork in (-1,1):
                    strut(base,top+pin_axis*fork*.034-B[:,2]*.040,.025,.025,'damper.support_web')
        with parent(lower_node):
            # Front eye is offset from the triangular arm plane; support it.
            if front:
                strut(bottom-[0, .05, .12], bottom+[0, -.05, .045], .045, .033,'damper.support_web')
            else:
                # The rear rod points aft from this eye. Put both fork feet
                # forward, with an offset arm saddle instead of a solid box
                # spanning the bearing center and obstructing its movement.
                B=g.basis(pin_axis);base=bottom+[s*.10,-.025,.030]
                g.box('damper.lower_inboard_bracket',base,(.050,.045,.120),coat,.005)
                for fork in (-1,1):
                    strut(base,bottom+pin_axis*fork*.034+B[:,2]*.040,.025,.025,'damper.support_web')
                for dz in (-.025,.025):
                    cylinder('damper.lower_bracket_pin',bottom+[s*.10,-.027,dz],bottom+[s*.10,.008,dz],.006,zinc,8)
        fixed_spherical_joint(f'damper_{i}_top_joint',body,top,pin_axis)
        fixed_spherical_joint(f'damper_{i}_lower_joint',lower_node,bottom,pin_axis,foot_direction=-1 if front else 1)
        M.joints[f'damper_{i}'] = {
            'a': top.tolist(), 'b': bottom.tolist(), 'mountNode': M.nodes[lower_node]['name'],
            'barrelEnd': barrel_end, 'rodLength': rod_length, 'restEyeDistance': d,
            'fixedMetalScale': [1, 1, 1], 'mountMotionRatio':.38 if front else .84,
            'movingEyeInboardOffset':0 if front else .10,'fixedPinAxis':pin_axis.tolist(),
            'bearingMisalignmentLimitDegrees':30}

    # A short pair of under-floor brackets replaces the cabin-height towers.
    # The transverse member lands on both actual rear rails at z=-2.00.
    with parent(body):
        frame_beam('chassis.rear_damper_crossmember',[-.5586,.3093,-2.0],[.5586,.3093,-2.0],.180,.095)

    # Bushes and retaining hardware make the four rear locating links legible.
    for name in ('rear_2_lower', 'rear_3_lower', 'rear_upper', 'rear_panhard'):
        with parent(ids[name]):
            for p in (M.joints[name]['a'], M.joints[name]['b']):
                eye(p, axis=(1, 0, 0), r=.027)

    with parent(ids['rear_axle']):
        for angle in np.linspace(0, math.tau, 10, endpoint=False):
            c = [math.sin(angle)*.091, HUB+math.cos(angle)*.091, -Z-.148]
            fastener(c, radius=.007, span=.012)

    # Real hydraulic equipment has separate electric motors, reservoir tanks,
    # pump blocks, check valves, dump solenoids, fittings and contactors.
    with parent(ids['trunk_equipment']):
        for z in (-2.25, -2.43):
            for x in (-.54, -.15):
                cylinder('hydraulic.motor_end_band', (x-.009, .48, z), (x+.009, .48, z), .077, zinc, 28)
            for angle in np.linspace(0, math.tau, 4, endpoint=False):
                p = np.array([-.55, .48+.060*math.sin(angle), z+.060*math.cos(angle)])
                cylinder('hydraulic.motor_tie_bolt', p, p+[.42, 0, 0], .003, zinc, 8)
            cylinder('hydraulic.reservoir_fill_neck', (.31, .55, z), (.31, .58, z), .015, brass, 12)
            cylinder('hydraulic.reservoir_hex_cap', (.31, .577, z), (.31, .590, z), .020, chrome, 6)
            cylinder('hydraulic.check_valve', (.035, .57, z), (.14, .57, z), .020, brass, 6)
            cylinder('hydraulic.check_inlet', (.025, .515, z), (.025, .57, z), .011, zinc, 8)
            for dz in (-.042, .042):
                p = np.array([.59, .54, z+dz])
                cylinder('hydraulic.dump_valve_stem', p, p+[0, .025, 0], .015, brass, 8)
                cylinder('hydraulic.dump_solenoid', p+[0, .025, 0], p+[0, .071, 0], .025, redcoat, 18)
                cylinder('hydraulic.dump_top_nut', p+[0, .071, 0], p+[0, .080, 0], .012, zinc, 6)
                tube('hydraulic.control_wire', [p+[0, .057, .021], p+[.04, .07, .03], [.73, .47, -2.02]], .0022, black, 7)
                cylinder('hydraulic.hose_crimp', (.69, .57, z+dz), (.735, .57, z+dz), .011, zinc, 12)
            tube('hydraulic.return_loop',[(.52,.49,z),(.55,.61,z),(.43,.64,z),(.42,.55,z)],.006,black,10)
            for x in (-.47, -.32, -.17):
                box('hydraulic.contactor_mount', (x,.40,z), (.07,.025,.07), coat, .005)
                cylinder('hydraulic.motor_contactor', (x,.41,z), (x,.47,z), .023, black, 18)
                for dz in (-.018,.018):
                    cylinder('hydraulic.contactor_terminal',(x,.47,z+dz),(x,.49,z+dz),.006,brass,8)

    add_service_bays(ctx, coat, zinc, brass, redcoat)
    refine_assemblies(ctx, coat, zinc, brass)
    refine_engine(ctx, coat, zinc)
    refine_springs_brakes(ctx,zinc)
    refine_ram_mounts(ctx,coat,zinc)
    from catrina_frame_pockets import add_frame_pockets
    add_frame_pockets(ctx,coat)
    form_frame_enclosures(ctx)
    route_exhaust_below_frame(ctx)
    reinforce_lid_inners(ctx)
    refine_slip_driveshaft(ctx,zinc)
    equipment=ids['trunk_equipment']
    M.nodes[equipment].setdefault('translation',[0,0,0])[2]-=.19
    M.origins[equipment][2]-=.19
    for p in M.parts:
        if p['name'].startswith('engine.radiator') or p['name']=='body.radiator_support':
            p['p'][:,2]-=.19
    M.nodes[body].setdefault('extras', {})['hardwareBasis'] = {
        'sources': 'docs/la-catrina/REAL-WORLD-BASIS.md',
        'customGeometry': True, 'damperCount': 4,
        'scope': 'catalog-inspired construction; no exact commercial part or certified fitment claim'}


def add_service_bays(ctx, coat, zinc, brass, redcoat):
    """Closed load-space skin above the axle, with serviceable equipment racks."""
    M, g, parent = ctx['M'], ctx['g'], ctx['parent']
    body, Z = ctx['body'], ctx['ZAXLE']
    box, cylinder, tube, torus = (ctx[k] for k in ('box', 'cylinder', 'tube', 'torus'))
    # Broad flat skins and small equipment cases do not need the coachwork's
    # dense corner sampling; three bevel steps retain their actual silhouette.
    box=g.box
    chrome, black, rubber, rose = (ctx[k] for k in ('chrome', 'black', 'rubber', 'rose'))
    ids = {n['name']: i for i, n in enumerate(M.nodes)}
    equipment = ids['trunk_equipment']
    liner = M.mat('plum_trunk_lining', 0x34162b, .74, 0)
    insert = M.mat('plum_trunk_panel', 0x461b37, .61, 0)
    cable = M.mat('battery_cable_insulation', 0x6a1534, .58, 0)
    M.parts[:] = [p for p in M.parts if p['parent'] != equipment and p['name'] not in (
        'body.trunk_center_floor', 'body.trunk_aft_floor', 'body.rear_cabin_tunnel','body.rear_bulkhead',
        'interior.rear_quarter_liner')]

    def wall(name, c, size, material=liner):
        box(name, c, size, material, .012)

    def housing(z, front):
        name = 'body.engine_wheelhouse' if front else 'body.trunk_wheelhouse'
        material = coat if front else liner
        for s in (-1, 1):
            # Closed inner cheek and crown, sized above maximum bump including
            # the tilted tire shoulder. Outer cheek meets the quarter liner.
            # The inner crown is relieved beneath the raised ram pocket;
            # a closed skin must not pass through the moving cylinder.
            limits=(-.31,.31)if front else(-.415,.170)
            pocket_inner=.449 if front else .345
            pocket_outer=.651 if front else .661
            angles=list(np.linspace(0,math.pi,56))
            angles+= [math.acos(d/.415)for d in limits if abs(d)<.415]
            rows = []
            for a in sorted(set(angles)):
                zz = z+.415*math.cos(a)
                y = max(.600, .42+.400*math.sin(a))
                rows.append([(s*.51,y,zz),(s*.54,y+.006,zz),(s*.89,y+.006,zz),(s*.93,y,zz)])
            for r0,r1 in zip(rows[:-1],rows[1:]):
                covered=limits[0]<=(r0[0][2]+r1[0][2])*.5-z<=limits[1]
                rr=[]
                for r in (r0,r1):
                    rr.append([(s*pocket_outer,r[1][1],r[0][2]),r[2],r[3]]if covered else r)
                if not covered:M.grid(name,rr,material,flip=s>0)
            # Inner wall has both faces, so no view through a one-sided skin.
            for r0,r1 in zip(rows[:-1],rows[1:]):
                covered=limits[0]<=(r0[0][2]+r1[0][2])*.5-z<=limits[1]
                xx=s*(pocket_inner if covered else .51)
                inner=[[(xx,.595,r[0][2]),(xx,.796 if covered else r[0][1],r[0][2])]for r in(r0,r1)]
                wallname=('body.engine_ram_inner_wall'if front else'body.trunk_ram_inner_wall')if covered else name
                M.grid(wallname,inner,material,flip=s>0);M.grid(wallname,inner,material,flip=s<0)
            # Close both ends of the inward return back to the unmodified
            # wheelhouse contour, including the ledge below the raised cap.
            retname='body.engine_ram_return'if front else'body.trunk_ram_return'
            for dz in limits:
                yy=max(.600,.42+.400*math.sqrt(max(0,1-(dz/.415)**2)));zz=z+dz
                lower=[[(s*pocket_inner,.595,zz),(s*.51,.595,zz)],[(s*pocket_inner,yy,zz),(s*.51,yy,zz)]]
                base=[(s*pocket_inner,yy,zz),(s*.51,yy,zz),(s*.54,yy+.006,zz),(s*pocket_outer,yy+.006,zz)]
                upper=[base,[(x,.796,zp)for x,yp,zp in base]]
                for panel in(lower,upper):
                    M.grid(retname,panel,material);M.grid(retname,panel,material,flip=True)
            for edge in (rows[0], rows[-1]):
                zz=edge[0][2]
                wall(name, (s*.72,.597,zz), (.42,.025,.028), material)
            # Upper ram head is hidden inside a formed, closed metal pocket.
            cover = 'body.engine_ram_cover' if front else 'body.trunk_ram_cover'
            x0,x1=sorted((s*pocket_inner,s*pocket_outer));z0,z1=z+limits[0],z+limits[1]
            # Open underneath: upper ring, cylinder and posts enter an actual
            # pocket, rather than piercing the bottom face of a solid box.
            def roof_y(xx,zz):
                if front:return .890
                back=-1.53-.065*(1-(xx/.916)**2)
                yback=.911+.008*(1-(xx/.916)**2)
                shelf=.860+(yback-.860)*(zz+1.23)/(back+1.23)
                return min(.890,shelf-.004)
            # The ram pocket is now one broad formed inner-fender blister.
            # Its outboard shoulder replaces (rather than overlays) the old
            # wheelhouse roof and the outer vertical cap wall. The inboard
            # lower seam, maximum crown and safe outer tub edge stay fixed.
            inner=pocket_inner;peak=.55 if front else .56
            roll=.024
            def wheel_y(xx,zz):
                crown=max(.600,.42+.400*math.sqrt(max(0,1-((zz-z)/.415)**2)))
                return crown+.006*min(1,max(0,(.93-xx)/.04))
            def crown_y(xx,zz):
                end=min(zz-z0,z1-zz)
                # Round down the end of the blister without moving the
                # tower posts; 30mm from either end has the full crown.
                u=min(1,max(0,end/roll))
                return roof_y(s*xx,zz)-roll*(1-math.sqrt(max(0,1-(1-u)**2)))
            # Each row runs from the preserved inner wall to the safe outer
            # wheelhouse seam. A tall elliptical inner shoulder replaces the
            # former flat cap side; the outboard half is a continuous dome.
            profile=[]
            for theta in np.linspace(0,math.pi/2,13):
                profile.append(('inner',inner+.060*(1-math.cos(theta)),theta))
            for xx in np.linspace(inner+.060,peak,4)[1:]:profile.append(('crown',xx,0))
            outerxs=sorted(set([*np.linspace(peak,.93,19)[1:],pocket_outer,.89]))
            for xx in outerxs:profile.append(('outer',xx,0))
            def upper_row(zz):
                row=[]
                for kind,xx,theta in profile:
                    high=crown_y(xx,zz)
                    if kind=='inner':yy=.796+(high-.796-(0 if front else .008))*math.sin(theta)
                    elif kind=='crown':
                        u=(xx-inner-.060)/(peak-inner-.060)
                        yy=high-(0 if front else .008)*(1-u)**2
                    else:
                        base=wheel_y(xx,zz);u=(xx-peak)/(.93-peak)
                        yy=base+max(0,high-base)*math.cos(u*math.pi/2)**2
                    row.append((s*xx,yy,zz))
                return row
            zs=sorted(set([*np.linspace(z0,z1,31),z0+roll,z1-roll]))
            dome=[upper_row(zz)for zz in zs]
            M.grid(cover,dome,material,flip=s<0)
            # Closed shaped end returns meet the old inner return and the
            # curved tub, with a real vertical step at the previous pocket
            # boundary. This closes the prior gap below the cap outer wall.
            for end,zz in enumerate((z0,z1)):
                top=upper_row(zz);lower=[];upper=[]
                for point,(_,xx,_)in zip(top,profile):
                    yy=.796 if xx<=pocket_outer+1e-10 else wheel_y(xx,zz)
                    upper.append(point);lower.append((s*xx,yy,zz))
                    if abs(xx-pocket_outer)<1e-10:
                        upper.append(point);lower.append((s*xx,wheel_y(xx,zz),zz))
                M.grid(cover,[lower,upper],material,flip=(s<0)==(end==0))


    with parent(body):
        # The cabin shift placed the last 35mm of this inner trim in the rear
        # tire sweep. A local lower notch clears it without moving the panel,
        # seats, exterior stamping or any suspension hardpoint.
        for s in (-1,1):
            box('interior.rear_quarter_liner',(s*.858,.560,-1.090),(.040,.565,.210),ctx['plum'],.006)
            box('interior.rear_quarter_liner',(s*.858,.72125,-1.220),(.040,.2425,.050),ctx['plum'],.006)
        # The rolled live axle sweeps inward below the rear bench. Narrow the
        # existing tunnel locally rather than relaxing the actual-pose check.
        # Formed under-bench pockets clear the forward-leaning rear springs.
        # Roof and side returns close the cabin while opening toward the
        # suspension below; the upper rear bulkhead remains continuous.
        wall('body.rear_cabin_tunnel',(0,.225,-1.0825),(.84,.065,.325),rose)
        for x,w in((0,.36),(-.395,.05),(.395,.05)):
            wall('body.rear_cabin_tunnel',(x,.225,-1.2725),(w,.065,.055),rose)
        for s in(-1,1):
            wall('body.trunk_ram_underbench_return',(s*.275,.356,-1.2745),(.190,.012,.059),rose)
            for x in(.176,.374):
                wall('body.trunk_ram_underbench_return',(s*x,.27125,-1.2745),(.008,.1575,.059),rose)
            wall('body.trunk_ram_underbench_return',(s*.275,.27125,-1.241),(.190,.1575,.008),rose)
        # Full closed trunk basin. Axle, links and springs remain below it.
        # Notches are occupied by closed lined frame-post sleeves. Their steel
        # load paths pass through openings, rather than through the floor skin.
        cuts=sorted([-1.970,-Z-.415,-Z+.170,-1.250])
        for za,zb in zip(cuts[:-1],cuts[1:]):
            near=-Z-.415<=(za+zb)*.5<=-Z+.170
            wall('body.trunk_center_floor',(0,.610,(za+zb)*.5),(.690 if near else 1.02,.032,zb-za))
        for s in(-1,1):
            for dz in(-.28,-.375):
                z=-Z+dz;x=s*.49
                # Four side returns join the floor and the raised top pocket.
                for a,b in(((x-.043,z-.036),(x+.043,z-.036)),((x+.043,z-.036),(x+.043,z+.036)),((x+.043,z+.036),(x-.043,z+.036)),((x-.043,z+.036),(x-.043,z-.036))):
                    M.mesh('body.trunk_ram_post_sleeve',[(a[0],.594,a[1]),(b[0],.594,b[1]),(b[0],.800,b[1]),(a[0],.800,a[1])],[(0,2,1),(0,3,2)],liner)
        wall('body.trunk_aft_floor', (0,.579,-2.3475), (1.82,.032,.795))
        wall('body.trunk_step', (0,.596,-1.965), (1.04,.063,.025))
        # The shifted rear bench needs a matching barrier. Its full width is
        # above the tire sweep; the lower panel fits between the wheelhouses.
        wall('body.rear_bulkhead',(0,.804,-1.290),(1.74,.168,.028),rose)
        wall('body.rear_bulkhead',(0,.535,-1.290),(1.02,.370,.028),rose)
        for x,w in((0,.36),(-.44,.14),(.44,.14)):
            wall('body.rear_bulkhead',(x,.305,-1.290),(w,.090,.028),rose)
        wall('body.trunk_front_bulkhead',(0,.804,-1.312),(1.80,.168,.014))
        wall('body.trunk_front_bulkhead',(0,.658,-1.312),(1.02,.124,.014))
        wall('body.trunk_rear_liner', (0,.685,-2.710), (1.80,.220,.030))
        for s in (-1,1):
            # A tapered closed wall stays below the rolling rear deck edge.
            rows=[]
            for z in np.linspace(-2.710,-1.276,24):
                top=min(.887,ctx['deck_height'](.905,z,False)-.035)
                lo,hi=s*.905-.016,s*.905+.016
                rows.append([(lo,.583,z),(hi,.583,z),(hi,top,z),(lo,top,z),(lo,.583,z)])
            M.grid('body.trunk_inner_quarter',rows,liner,flip=True)
            for row,sign in ((rows[0],-1),(rows[-1],1)):
                f=[(0,1,2),(0,2,3)]if sign>0 else[(0,2,1),(0,3,2)]
                M.mesh('body.trunk_inner_quarter',row[:4],f,liner)
            wall('body.trunk_lining_insert', (s*.883,.708,-2.415), (.008,.160,.552), insert)
            for z in (-2.66,-2.23):
                cylinder('body.trunk_panel_fastener', (s*.876,.752,z), (s*.867,.752,z), .008, zinc, 8)
        # Trace the actual mesh boundary. Equal-Z vertex groups are not
        # sections on a curved/clipped grid and produced zigzag interior seals.
        lid=next(p for p in M.parts if p['name']=='body.trunk')
        verts=lid['p']+M.origins[lid['parent']]
        faces=lid['f'];edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
        edges,count=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
        adjacent={}
        for a,b in edges[count==1]:
            adjacent.setdefault(int(a),[]).append(int(b));adjacent.setdefault(int(b),[]).append(int(a))
        assert adjacent and all(len(v)==2 for v in adjacent.values()),'Trunk skin boundary is not a closed manifold loop'
        unused=set(adjacent);loops=[]
        while unused:
            first=min(unused);loop=[first];previous=None;current=first
            while True:
                nxt=next(v for v in adjacent[current] if v!=previous)
                if nxt==first:break
                assert nxt not in loop,'Trunk skin boundary repeats before closing'
                loop.append(nxt);previous,current=current,nxt
            unused.difference_update(loop);loops.append(verts[loop][:,[0,2]])
        def area(p):return .5*np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
        boundary=max(loops,key=lambda p:abs(area(p)))
        tangent=np.roll(boundary,-1,axis=0)-boundary;tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        inward=np.c_[-tangent[:,1],tangent[:,0]]*(1 if area(boundary)>0 else -1)
        prev=np.roll(inward,1,axis=0)
        inset=boundary+(prev+inward)*(.015/(1+(prev*inward).sum(1)))[:,None]
        seal=[]
        for a,b in zip(inset,np.roll(inset,-1,axis=0)):
            for t in np.linspace(0,1,max(1,int(math.ceil(np.linalg.norm(b-a)/.030))),endpoint=False):
                x,z=a*(1-t)+b*t
                seal.append((x,ctx['deck_height'](x,z,False)-.029,z))
        seal.append(seal[0])
        tube('body.trunk_weather_seal',seal,.006,rubber,8)
        housing(-Z, False)
        for x in (-.37,0,.37):
            tube('body.trunk_floor_bead',[(x,.629,-1.28),(x,.629,-1.86)],.0035,insert,8)
        # Closed engine bay inner fenders and radiator support. This leaves
        # the central engine and dress-up parts visible above the lower pan.
        for s in (-1,1):
            # A full rectangular inner wall intersects the turned tire at
            # bump. Its lower edge now follows the existing wheelhouse crown.
            rows=[]
            for a in np.linspace(0,math.pi,56):
                zz=Z+.415*math.cos(a)
                yy=max(.600,.42+.400*math.sin(a))+.006
                rows.append([(s*.905,yy,zz),(s*.905,.885,zz)])
            M.grid('body.engine_inner_fender',rows,rose,flip=s>0)
            M.grid('body.engine_inner_fender',rows,rose,flip=s<0)
            for za,zb in ((.65,Z-.415),(Z+.415,2.26)):
                rows=[]
                for zz in np.linspace(za,zb,12):
                    top=min(.885,ctx['deck_height'](.905,zz,True)-.030)
                    lo,hi=s*.905-.016,s*.905+.016
                    rows.append([(lo,.345,zz),(hi,.345,zz),(hi,top,zz),(lo,top,zz),(lo,.345,zz)])
                M.grid('body.engine_inner_fender',rows,rose,flip=True)
                for row,sign in ((rows[0],-1),(rows[-1],1)):
                    f=[(0,1,2),(0,2,3)]if sign>0 else[(0,2,1),(0,3,2)]
                    M.mesh('body.engine_inner_fender',row[:4],f,rose)
        housing(Z, True)
        wall('body.engine_lower_pan',(0,.315,1.45),(.62,.035,1.59),coat)
        wall('body.radiator_support',(0,.592,2.411),(1.80,.458,.045),coat)
        box('engine.radiator',(0,.573,2.345),(.71,.40,.060),black,.012)
        for x in np.linspace(-.32,.32,34):
            cylinder('engine.radiator_fin',(x,.403,2.307),(x,.743,2.307),.0016,zinc,6)
        cylinder('engine.radiator_cap',(0,.787,2.345),(0,.800,2.345),.023,chrome,10)
        tube('engine.coolant_hose',[(.23,.733,2.30),(.29,.735,2.10),(.20,.66,1.86)],.024,rubber,12)

    # Components are laid out from front to rear: retained battery row,
    # then two full polished motor/pump/tank assemblies visible from the rear.
    with parent(equipment):
        wall('hydraulic.equipment_rack', (0,.618,-2.205), (1.58,.035,.66), chrome)
        for x in (-.75,.75):
            wall('hydraulic.rack_sill',(x,.650,-2.204),(.035,.035,.65),chrome)
        for z in (-1.900,-2.205,-2.500):
            wall('hydraulic.rack_crossrail',(0,.650,z),(1.53,.027,.024),chrome)
        for x in (-.48,-.16,.16,.48):
            wall('hydraulic.battery',(x,.738,-2.020),(.265,.215,.205),black)
            wall('hydraulic.battery_lid',(x,.850,-2.020),(.273,.025,.214),insert)
            for s in (-1,1):
                cylinder('hydraulic.battery_terminal',(x+s*.083,.861,-2.020),(x+s*.083,.877,-2.020),.009,zinc,12)
                tube('hydraulic.battery_lead',[(x+s*.083,.878,-2.020),(x+s*.10,.884,-1.955),(x+s*.12,.798,-1.895)],.005,cable if s<0 else black,10)
            wall('hydraulic.battery_hold_down',(x,.870,-2.020),(.023,.015,.231),chrome)
            for z in (-2.135,-1.905):
                cylinder('hydraulic.battery_hold_down_rod',(x,.640,z),(x,.875,z),.0035,zinc,8)
                cylinder('hydraulic.battery_wingnut',(x-.010,.877,z),(x+.010,.877,z),.004,chrome,8)
        for z in (-2.225,-2.425):
            y=.734
            # Broad tank and electric motor separated by a compact brass block.
            cylinder('hydraulic.chrome_motor',(-.56,y,z),(-.15,y,z),.065,chrome,40)
            cylinder('hydraulic.motor_endcap',(-.575,y,z),(-.55,y,z),.068,chrome,32)
            cylinder('hydraulic.gold_pump',(-.15,y,z),(.055,y,z),.061,brass,32)
            cylinder('hydraulic.reservoir',(.075,y,z),(.51,y,z),.070,chrome,40)
            for x,r in ((-.55,.067),(-.17,.067),(.085,.072),(.50,.072)):
                cylinder('hydraulic.end_band',(x-.008,y,z),(x+.008,y,z),r,zinc,32)
            for a in np.linspace(0,math.tau,4,endpoint=False):
                p=np.array([-.56,y+.053*math.sin(a),z+.053*math.cos(a)])
                cylinder('hydraulic.motor_tie_bolt',p,p+[.41,0,0],.0028,zinc,8)
            for x in (-.43,.36):
                wall('hydraulic.pump_mount',(x,.666,z),(.085,.058,.12),coat)
                for dx in (-.029,.029):
                    cylinder('hydraulic.mount_bolt',(x+dx,.638,z),(x+dx,.650,z),.007,zinc,6)
            cylinder('hydraulic.reservoir_fill_neck',(.31,.796,z),(.31,.823,z),.014,brass,12)
            cylinder('hydraulic.reservoir_hex_cap',(.31,.820,z),(.31,.834,z),.020,chrome,6)
            wall('hydraulic.valve_bank',(.60,.705,z),(.13,.125,.12),brass)
            cylinder('hydraulic.check_valve',(.015,.810,z),(.136,.810,z),.017,brass,6)
            tube('hydraulic.check_feed',[(.025,.773,z),(.025,.811,z),(.14,.811,z),(.17,.773,z)],.009,zinc,10)
            for dz in (-.036,.036):
                p=np.array([.60,.770,z+dz])
                cylinder('hydraulic.dump_valve_stem',p,p+[0,.022,0],.013,brass,10)
                cylinder('hydraulic.dump_solenoid',p+[0,.022,0],p+[0,.060,0],.021,redcoat,20)
                cylinder('hydraulic.dump_top_nut',p+[0,.060,0],p+[0,.068,0],.009,zinc,6)
                cylinder('hydraulic.hose_crimp',(.650,.748,z+dz),(.692,.748,z+dz),.010,zinc,12)
                tube('hydraulic.pressure_line',[(.688,.748,z+dz),(.77,.77,z+dz),(.79,.834,z+.06),(.79,.832,-1.73),(.73,.79,-1.70)],.0055,black,10)
                tube('hydraulic.control_wire',[p+[0,.05,.018],p+[.055,.06,.024],[.72,.68,z+.03]],.0022,cable,8)
            tube('hydraulic.return_loop',[(.54,.706,z),(.56,.840,z),(.45,.864,z),(.42,.805,z)],.006,black,10)
            for zz in (z-.06,z,z+.06):
                wall('hydraulic.contactor_mount',(-.665,.666,zz),(.075,.018,.05),coat)
                cylinder('hydraulic.motor_contactor',(-.665,.675,zz),(-.665,.721,zz),.019,black,16)
                for dx in (-.011,.011):
                    cylinder('hydraulic.contactor_terminal',(-.665+dx,.721,zz),(-.665+dx,.735,zz),.0045,brass,8)
        for s in (-1,1):
            torus('hydraulic.bulkhead_grommet',(s*.73,.79,-1.70),.014,.004,rubber,axis=(0,0,1),segments=20,sides=8)


def refine_assemblies(ctx, coat, zinc, brass):
    """Formed castings, pressed arms and mounted hydraulic fittings.

    All existing pivot transforms and validated tire-clearance skins are kept.
    This pass changes the visible construction of parts around those pivots.
    """
    M,g,parent=ctx['M'],ctx['g'],ctx['parent']
    body,Z,H=ctx['body'],ctx['ZAXLE'],ctx['HUB']
    box,cylinder,tube,torus=(ctx[k]for k in ('box','cylinder','tube','torus'))
    small_box=g.box
    chrome,rubber,black,plum=(ctx[k]for k in ('chrome','rubber','black','plum'))
    ids={n['name']:i for i,n in enumerate(M.nodes)}
    brushed=M.mat('formed_suspension_steel',0x8c9294,.31,.88)
    cast=M.mat('cast_axle_enamel',0x383a3c,.53,0)
    cable=M.mat('power_cable_red',0x741728,.47,0)

    def bolt(c,axis=(1,0,0),r=.011):
        c=np.array(c,float);axis=np.array(axis,float)
        cylinder('fitting.hex_bolt',c-axis*.004,c+axis*.007,r,zinc,6)

    def plate(name,xy,z,depth,mat):
        # Separate polygon faces preserve the broad plate's flat normal.
        p=np.array(xy,float)
        area=sum(p[j,0]*p[(j+1)%len(p),1]-p[(j+1)%len(p),0]*p[j,1]for j in range(len(p)))
        if area<0:p=p[::-1]
        for sign in (-1,1):
            verts=np.c_[p[:,0],p[:,1],np.full(len(p),z+sign*depth/2)]
            faces=[(0,j,j+1)if sign>0 else(0,j+1,j)for j in range(1,len(p)-1)]
            M.mesh(name,verts,faces,mat,normals=np.tile([0,0,sign],(len(p),1)))
        for j in range(len(p)):
            a,b=p[j],p[(j+1)%len(p)]
            v=[[a[0],a[1],z-depth/2],[b[0],b[1],z-depth/2],[b[0],b[1],z+depth/2],[a[0],a[1],z+depth/2]]
            M.mesh(name,v,[(0,1,2),(0,2,3)],mat)

    def smooth_hose(name,controls,rad,mat):
        p=np.array(controls,float)
        ts=np.linspace(0,1,13)
        pts=[(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]for t in ts]
        tube(name,pts,rad,mat,8)

    # Broad frame feet anchor the open fork-side supports authored above.
    # The old tall side plates crossed the shock sweep and are omitted.
    with parent(body):
        for i in range(4):
            s=-1 if i%2==0 else 1;front=i<2
            x0=.57 if front else .20
            y0=.27 if front else .31;zz=Z+.12 if front else -2.00
            box('damper.tower_foot',(s*x0,y0+.018,zz),(.21,.026,.16 if front else .20),coat,.006)

    # Curved pressed-channel arm legs surround a separate spring pocket.
    for i in range(2):
        s=-1 if i==0 else 1
        for upper in (False,True):
            node=ids[f'front_{i}_'+('upper'if upper else'lower')]
            M.parts[:]=[p for p in M.parts if not(p['parent']==node and p['name']=='hardware.boxed_bracket')]
            y=.43 if upper else .25;span=.16 if upper else .22
            a=np.array([s*.18,y,Z]);b=np.array([s*.715,y,Z])
            width=.058 if upper else .074;depth=.028 if upper else .038;th=.006
            profile=[(-width/2,depth/2),(-width/2,-depth/2),(width/2,-depth/2),(width/2,depth/2),(width/2-th,depth/2),(width/2-th,-depth/2+th),(-width/2+th,-depth/2+th),(-width/2+th,depth/2)]
            with parent(node):
                for sign in (-1,1):
                    controls=np.array([a+[0,0,sign*span],a+[s*.19,0,sign*span],b+[-s*.15,0,sign*.075],b])
                    rows=[]
                    for t in np.linspace(0,1,15):
                        c=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
                        tangent=3*(1-t)**2*(controls[1]-controls[0])+6*(1-t)*t*(controls[2]-controls[1])+3*t*t*(controls[3]-controls[2]);tangent/=np.linalg.norm(tangent)
                        across=np.array([-tangent[2],0,tangent[0]])
                        rows.append([c+across*xx+[0,yy,0]for xx,yy in profile+[profile[0]]])
                    M.grid('front.formed_channel_arm',rows,brushed)
                if not upper:
                    c=a+(b-a)*.69
                    torus('front.spring_pocket_rim',c+[0,.014,0],.067,.005,brushed,axis=(0,1,0),segments=28,sides=8)
                    cylinder('front.spring_pocket_draw',c+[0,-.011,0],c+[0,.012,0],.071,brushed,28,r2=.066)
        # A waisted cast carrier joins the two ball-joint centers to the hub.
        # Its existing upright node still owns the exact same end points.
        upright=ids[f'upright_{i}']
        M.parts[:]=[p for p in M.parts if not(p['parent']==upright and p['name']=='front.upright')]
        with parent(upright):
            rows=[]
            for y,r,offset in ((.25,.024,0),(.275,.031,.003),(.300,.039,.006),(.335,.031,.003),(.400,.024,0),(.43,.023,0)):
                rows.append([(s*(.715+offset)+r*math.sin(t),y,Z+r*.83*math.cos(t))for t in np.linspace(0,math.tau,21)])
            M.grid('front.upright',rows,cast,flip=True)
            cylinder('front.spindle_bearing',(s*.714,H,Z),(s*.765,H,Z),.036,brushed,24,r2=.027)
            for y in (.25,.43):
                cylinder('front.ball_joint_socket',(s*.715,y-.009,Z),(s*.715,y+.009,Z),.027,cast,20)

    # Cast pumpkin and domed pressed cover, with an irregular bolted flange.
    axle=ids['rear_axle']
    M.parts[:]=[p for p in M.parts if not(p['parent']==axle and(p['name'] in ('axle.differential','axle.diff_cover')or p['name'].startswith('hardware.')))]
    with parent(axle):
        rings=[(-.153,.131,.121),(-.125,.155,.138),(-.065,.168,.145),(.015,.158,.142),(.085,.118,.103),(.15,.062,.057),(.19,.043,.041)]
        rows=[]
        for z,rx,ry in rings:
            rows.append([(rx*math.sin(t)*(1+.04*math.cos(t)),H+ry*math.cos(t),-Z+z)for t in np.linspace(0,math.tau,37)])
        M.grid('axle.differential',rows,cast)
        flange=[]
        for r in (1.0,1.105):
            flange.append([(r*.132*math.sin(t)*(1+.06*math.cos(t)),H+r*.122*math.cos(t),-Z-.156)for t in np.linspace(0,math.tau,37)])
        M.grid('axle.cover_flange',flange,zinc)
        rows=[]
        for radius,zz in ((.01,-.205),(.32,-.201),(.65,-.187),(.91,-.165),(1,-.158)):
            rows.append([(radius*.132*math.sin(t)*(1+.06*math.cos(t)),H+radius*.122*math.cos(t),-Z+zz)for t in np.linspace(0,math.tau,37)])
        M.grid('axle.diff_cover',rows,cast)
        cylinder('axle.cover_center',(0,H,-Z-.203),(0,H,-Z-.206),.002,cast,12)
        for t in np.linspace(0,math.tau,12,endpoint=False):
            bolt((.142*math.sin(t)*(1+.06*math.cos(t)),H+.131*math.cos(t),-Z-.162),(0,0,-1),.009)
        cylinder('axle.fill_plug',(.045,H+.012,-Z-.202),(.045,H+.012,-Z-.214),.014,zinc,6)
        for s in (-1,1):
            cylinder('axle.cast_tube_transition',(s*.125,H,-Z),(s*.235,H,-Z),.063,cast,24,r2=.041)
            torus('axle.tube_weld',(s*.235,H,-Z),.041,.0035,cast,axis=(1,0,0),segments=24,sides=6)
            # Folded saddle walls give the existing seat thickness and ears.
            for dx in (-.069,.069):
                box('axle.spring_saddle_cheek',(s*.56+dx,H+.031,-Z),(.009,.075,.15),coat,.005)
            for dz in (-.065,.065):
                bolt((s*.56,H+.070,-Z+dz),(0,1,0),.009)

    # Rear locating links are formed channels with cylindrical bushing eyes.
    for name in ('rear_2_lower','rear_3_lower','rear_upper'):
        node=ids[name];a=np.array(M.joints[name]['a']);b=np.array(M.joints[name]['b']);axis=(b-a)/np.linalg.norm(b-a)
        across=np.cross(axis,[0,1,0]);across/=np.linalg.norm(across);up=np.cross(across,axis);B=np.c_[across,axis,up]
        M.parts[:]=[p for p in M.parts if not(p['parent']==node and(p['name'].startswith(('rear.trailing_link','driveline.rear_upper','hardware.'))))]
        length=np.linalg.norm(b-a)-.09
        with parent(node):
            box('rear.link_channel_web',(a+b)*.5-up*.015,(.062,length,.007),brushed,.003,B=B)
            for sign in (-1,1):box('rear.link_channel_edge',(a+b)*.5+across*sign*.028,(.007,length,.037),brushed,.003,B=B)
            for p in (a,b):
                cylinder('rear.link_eye_outer',p+[-.032,0,0],p+[.032,0,0],.030,brushed,20)
                for sign in (-1,1):
                    cylinder('rear.link_rubber_bush',p+[sign*.030,0,0],p+[sign*.038,0,0],.023,rubber,18)
                    cylinder('rear.link_bush_sleeve',p+[sign*.038,0,0],p+[sign*.044,0,0],.014,zinc,16)
                    bolt(p+[sign*.047,0,0],(sign,0,0),.012)
        # Fixed frame-side clevises stop the eye from appearing welded to air.
        with parent(body):
            for sign in (-1,1):
                small_box('rear.link_frame_clevis',a+[sign*.049,-.012,0],(.010,.080,.090),coat,.005)
            if abs(a[0])>.1:
                # Fixed rail-to-clevis bridge gives each lower trailing arm a
                # load path into the X rail rather than a floating frame eye.
                s=1 if a[0]>0 else-1
                start=np.array([s*.1994,.258,-.45]);end=a+[0,-.047,0]
                small_box('rear.link_frame_bridge',(start+end)*.5,(.066,float(np.linalg.norm(end-start))+.025,.070),coat,.005,B=g.basis(end-start))
            else:
                small_box('rear.upper_mount_crossmember',(0,.298,-.45),(.43,.080,.090),coat,.006)
                for sign in (-1,1):
                    small_box('rear.upper_mount_web',(sign*.049,.370,-.45),(.010,.165,.110),coat,.004)
        with parent(axle):
            for sign in (-1,1):
                small_box('axle.link_mount_ear',b+[sign*.046,-.017,0],(.010,.086,.091),coat,.004)
            if name=='rear_upper':
                small_box('axle.upper_link_pedestal',b+[0,-.045,0],(.118,.065,.102),cast,.009)

    # A machined manifold is a block with separate ports, not another barrel.
    equipment=ids['trunk_equipment']
    M.parts[:]=[p for p in M.parts if not(p['parent']==equipment and p['name'].startswith(('hydraulic.gold_pump','hydraulic.pressure_line','hydraulic.control_wire','hydraulic.return_loop','hydraulic.battery_lead','hydraulic.bulkhead_grommet')))]
    with parent(equipment):
        for z in (-2.225,-2.425):
            y=.734
            box('hydraulic.gold_pump',(-.055,y,z),(.14,.115,.125),brass,.009)
            cylinder('hydraulic.motor_coupling',(-.15,y,z),(-.125,y,z),.029,chrome,20)
            cylinder('hydraulic.reservoir_coupling',(.015,y,z),(.076,y,z),.027,chrome,20)
            for zz in (z-.064,z+.064):
                for xx in (-.100,-.010):bolt((xx,y+.031,zz),(0,0,1),.007)
            cylinder('hydraulic.manifold_port',(-.055,y+.055,z),(-.055,y+.082,z),.017,brass,6)
            cylinder('hydraulic.motor_rear_hub',(-.589,y,z),(-.575,y,z),.029,zinc,20)
            for a in np.linspace(0,math.tau,10,endpoint=False):
                p=np.array([-.591,y+.047*math.sin(a),z+.047*math.cos(a)])
                cylinder('hydraulic.motor_vent',p,p+[.003,0,0],.006,black,8)
            for x in (-.43,.36):
                for sign in (-1,1):
                    cylinder('hydraulic.saddle_stud',(x,.645,z+sign*.052),(x,.690,z+sign*.052),.004,zinc,8)
                    bolt((x,.695,z+sign*.052),(0,1,0),.008)
            # Wide smooth hose loops and crimped ends are visible from above.
            for dz in (-.036,.036):
                endy=.770+dz*.70;endz=-1.70 if z>-2.3 else-1.84
                smooth_hose('hydraulic.pressure_line',[(.69,.748,z+dz),(.86,.79,z+.04),(.82,.86,endz-.10),(.886,endy,endz)],.006,black)
                torus('hydraulic.bulkhead_grommet',(.887,endy,endz),.012,.004,rubber,axis=(1,0,0),segments=16,sides=6)
                cylinder('hydraulic.bulkhead_union',(.869,endy,endz),(.892,endy,endz),.009,brass,6)
                smooth_hose('hydraulic.control_wire',[(.60,.82,z+dz),(.70,.85,z+.05),(.73,.73,z+.09),(.70,.68,z+.04)],.0022,cable)
            smooth_hose('hydraulic.return_loop',[(.54,.706,z),(.62,.878,z+.01),(.41,.885,z+.01),(.42,.805,z)],.006,black)
        for s in (-1,1):
            box('hydraulic.power_junction',(s*.70,.810,-2.035),(.075,.075,.065),black,.008)
            box('hydraulic.junction_face',(s*.70,.810,-2.072),(.073,.069,.008),zinc,.003)
            for dx in (-.024,.024):
                for dy in (-.023,.023):bolt((s*.70+dx,.810+dy,-2.078),(0,0,-1),.0045)
            for dx in (-.018,.018):
                cylinder('hydraulic.junction_lug',(s*.70+dx,.841,-2.035),(s*.70+dx,.856,-2.035),.006,brass,10)
            box('hydraulic.junction_bracket',(s*.70,.725,-2.035),(.025,.14,.040),coat,.004)
        for x0,x1 in ((-.48,-.16),(.16,.48)):
            smooth_hose('hydraulic.battery_series_link',[(x0+.083,.878,-2.020),(x0+.13,.888,-1.955),(x1-.13,.888,-1.955),(x1-.083,.878,-2.020)],.0055,cable)
        for x,s in ((-.48,-1),(-.16,-1),(.16,1),(.48,1)):
            sign=-1 if x<0 else 1
            smooth_hose('hydraulic.battery_lead',[(x+sign*.083,.878,-2.020),(x+sign*.12,.886,-2.02),(s*.70,.870,-2.035),(s*.70,.854,-2.035)],.0055,black if abs(x)<.3 else cable)
            box('hydraulic.battery_front_strap',(x,.753,-2.130),(.026,.235,.008),plum,.003)


def refine_engine(ctx,coat,zinc):
    """Small-block component construction, within the existing engine envelope.

    Visual material basis: Chevrolet Performance's 350 engine specifications
    identify an iron block/heads, aluminum intake and a separate water pump:
    https://www.chevrolet.com/performance-parts/crate-engines/small-block-engines/350-engine
    This is an original simplified assembly, not a replica or a power claim.
    """
    M,g,parent=ctx['M'],ctx['g'],ctx['parent'];body=ctx['body']
    cylinder,tube,torus=(ctx[k]for k in ('cylinder','tube','torus'))
    chrome,rubber,black=(ctx[k]for k in ('chrome','rubber','black'))
    # Use the lower-density bevel helper for small castings, hidden flanges and
    # fasteners. The dense coachwork radii are unnecessary at these dimensions.
    box=g.box
    iron=next(i for i,m in enumerate(M.materials)if m['name'].endswith('cast_axle_enamel'))
    alloy=next(i for i,m in enumerate(M.materials)if m['name'].endswith('formed_suspension_steel'))
    M.parts[:]=[p for p in M.parts if p['name']not in ('driveline.V8_block','engine.radiator','engine.radiator_fin','engine.radiator_cap','engine.coolant_hose')]

    def hose(name,controls,r,material=rubber,steps=15,sides=10):
        p=np.array(controls,float)
        pts=[(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]for t in np.linspace(0,1,steps)]
        tube(name,pts,r,material,sides)
        return np.array(pts)

    def clamp(p,axis,r):
        p=np.array(p);axis=np.array(axis);axis=axis/np.linalg.norm(axis)
        cylinder('engine.hose_clamp',p-axis*.004,p+axis*.004,r,zinc,16,caps=False)
        box('engine.clamp_screw',p+[0,r,0],(.015,.007,.008),zinc,.001)

    with parent(body):
        # Narrow crankcase with separate inclined cylinder banks and heads.
        rows=[]
        for z,scale in ((1.255,.91),(1.28,1),(1.80,1),(1.825,.91)):
            rows.append([(scale*.170*math.sin(t),.444+scale*.105*math.cos(t),z)for t in np.linspace(0,math.tau,21)])
        M.grid('driveline.V8_block',rows,iron)
        for ring,sign in ((rows[0],-1),(rows[-1],1)):
            points=[(0,.444,ring[0][2])]+ring
            faces=[(0,j,j+1)if sign<0 else(0,j+1,j)for j in range(1,21)]
            M.mesh('driveline.V8_block',points,faces,iron)
        cylinder('engine.bellhousing_flange',(0,.430,1.218),(0,.430,1.280),.151,iron,20,r2=.140)
        for s in (-1,1):
            B=g.rotZ(s*.4)
            box('engine.cylinder_bank',(s*.104,.515,1.545),(.185,.175,.530),iron,.025,B=B)
            box('engine.head_gasket',(s*.144,.579,1.545),(.217,.008,.554),black,.002,B=B)
            box('engine.cylinder_head',(s*.151,.597,1.545),(.219,.045,.554),iron,.012,B=B)
            for z in (1.34,1.535,1.73):
                cylinder('engine.core_plug',(s*.230,.455,z),(s*.240,.459,z),.023,zinc,16)
            for z in (1.31,1.46,1.61,1.76):
                cylinder('engine.exhaust_port',(s*.211,.548,z),(s*.254,.494,z),.019,iron,12)
                cylinder('engine.spark_plug',(s*.220,.566,z),(s*.246,.575,z),.007,zinc,10)
                angle=math.tau*((z-1.31)/.15+(0 if s<0 else 4))/8
                lead_start=(.030*math.sin(angle),.727,1.225+.030*math.cos(angle))
                hose('engine.ignition_lead',[lead_start,(s*.16,.755,1.24),(s*.265,.665,z),(s*.248,.575,z)],.0035,black,9,6)
            cylinder('engine.exhaust_manifold',(s*.254,.494,1.29),(s*.254,.494,1.79),.025,iron,16)
            cylinder('engine.exhaust_collector',(s*.254,.494,1.40),(s*.22,.38,1.40),.027,iron,16)
            # The mounts terminate on the fixed front rail, not the wishbones.
            cylinder('engine.mount_boss',(s*.13,.415,1.69),(s*.22,.390,1.69),.033,iron,14)
            box('engine.mount_isolator',(s*.25,.370,1.69),(.082,.040,.075),rubber,.006)
            box('engine.mount_bracket',(s*.405,.326,1.69),(.32,.055,.085),coat,.005)
        box('engine.oil_pan_flange',(0,.329,1.535),(.322,.016,.584),zinc,.006)
        box('engine.oil_pan_sump',(0,.283,1.43),(.276,.096,.332),iron,.026)
        box('engine.oil_pan_front',(0,.305,1.725),(.276,.050,.250),iron,.015)
        cylinder('engine.oil_drain_plug',(0,.240,1.30),(0,.230,1.30),.010,zinc,6)
        for s in (-1,1):
            for z in (1.29,1.44,1.59,1.74):
                cylinder('engine.pan_bolt',(s*.145,.336,z),(s*.145,.342,z),.006,zinc,6)
        # The intake valley and carburetor connect the round air cleaner to
        # both banks instead of leaving it balanced on a solid cuboid.
        box('engine.intake_plenum',(0,.620,1.545),(.155,.055,.335),alloy,.015)
        for s in (-1,1):
            for z in (1.35,1.46,1.63,1.74):
                cylinder('engine.intake_runner',(s*.045,.637,1.545+(z-1.545)*.55),(s*.135,.615,z),.020,alloy,12)
        box('engine.carburetor',(0,.670,1.54),(.122,.060,.142),zinc,.008)
        cylinder('engine.distributor_stem',(0,.610,1.225),(0,.685,1.225),.020,iron,14)
        cylinder('engine.distributor_cap',(0,.682,1.225),(0,.718,1.225),.042,black,20)
        for a in np.linspace(0,math.tau,8,endpoint=False):
            p=np.array([.030*math.sin(a),.710,1.225+.030*math.cos(a)])
            cylinder('engine.distributor_terminal',p,p+[0,.017,0],.006,black,8)
        # Separate timing cover, water pump, alternator and two driven pulleys.
        cylinder('engine.timing_cover',(0,.450,1.823),(0,.450,1.850),.112,alloy,24)
        cylinder('engine.crank_pulley',(0,.405,1.852),(0,.405,1.966),.066,iron,24)
        cylinder('engine.water_pump',(0,.560,1.835),(0,.560,1.912),.060,iron,20,r2=.038)
        cylinder('engine.water_pump_pulley',(0,.560,1.918),(0,.560,1.970),.047,iron,24)
        cylinder('engine.alternator',(-.263,.600,1.790),(-.263,.600,1.920),.055,alloy,24)
        cylinder('engine.alternator_pulley',(-.263,.600,1.920),(-.263,.600,1.968),.040,iron,20)
        box('engine.alternator_bracket',(-.194,.545,1.815),(.165,.025,.055),coat,.005,B=g.rotZ(-.52))
        belt=[(0,.334),(.055,.361),(.068,.405),(.045,.565),(.016,.606),(-.263,.642),(-.300,.620),(-.301,.580),(-.276,.560),(-.038,.350),(0,.334)]
        tube('engine.accessory_belt',[(x,y,1.950)for x,y in belt],.0045,rubber,8)
        for z in (1.941,1.959):
            torus('engine.pulley_groove',(0,.405,z),.065,.003,alloy,axis=(0,0,1),segments=24,sides=5)
        cylinder('engine.fan_hub',(0,.560,1.966),(0,.560,2.085),.023,zinc,16)
        for a in np.linspace(0,math.tau,6,endpoint=False):
            B=g.rotZ(a)@g.rotY(.28)
            box('engine.fan_blade',(-.098*math.sin(a),.560+.098*math.cos(a),2.080),(.052,.137,.006),coat,0,B=B)
        # A separate top/bottom tank and recessed fin pack gives the radiator
        # depth; its hose necks terminate on the tanks and water-pump fittings.
        box('engine.radiator_core',(0,.574,2.345),(.640,.330,.040),iron,.004)
        for y in np.linspace(.416,.732,38):
            box('engine.radiator_fin',(0,y,2.319),(.638,.0013,.015),coat,0)
        for x in np.linspace(-.306,.306,22):
            box('engine.radiator_tube',(x,.574,2.316),(.0024,.323,.009),alloy,0)
        for y in (.388,.760):
            box('engine.radiator_tank',(0,y,2.345),(.697,.055,.080),coat,.014)
        for s in (-1,1):
            box('engine.radiator_side_channel',(s*.343,.574,2.345),(.023,.350,.080),zinc,.004)
        cylinder('engine.radiator_fill_neck',(0,.785,2.345),(0,.805,2.345),.019,zinc,16)
        cylinder('engine.radiator_cap',(0,.804,2.345),(0,.812,2.345),.025,chrome,16)
        box('engine.radiator_cap_ears',(0,.809,2.345),(.067,.008,.016),chrome,.003)
        cylinder('engine.radiator_upper_neck',(.21,.750,2.345),(.21,.750,2.266),.023,zinc,16)
        cylinder('engine.thermostat_housing',(0,.622,1.835),(0,.666,1.835),.032,alloy,16,r2=.022)
        top=hose('engine.coolant_hose',[(.21,.750,2.080),(.24,.800,1.93),(.04,.780,1.89),(0,.665,1.835)],.024)
        clamp(top[1],top[2]-top[0],.025);clamp(top[-2],top[-1]-top[-3],.025)
        cylinder('engine.radiator_lower_neck',(-.21,.392,2.345),(-.21,.392,2.275),.023,zinc,16)
        cylinder('engine.pump_lower_neck',(-.040,.525,1.875),(-.100,.495,1.895),.023,alloy,16)
        lower=hose('engine.lower_coolant_hose',[(-.21,.392,2.086),(-.28,.380,1.95),(-.27,.450,1.95),(-.10,.495,1.895)],.024)
        clamp(lower[1],lower[2]-lower[0],.025);clamp(lower[-2],lower[-1]-lower[-3],.025)


def refine_springs_brakes(ctx,zinc):
    """Continuous coil normals, rigid pressed seats and complete drum faces."""
    M,parent,g=ctx['M'],ctx['parent'],ctx['g'];body=ctx['body']
    cylinder,tube,torus=(ctx[k]for k in ('cylinder','tube','torus'))
    chrome,steel,red,rubber=(ctx[k]for k in ('chrome','steel','red','rubber'))
    ids={n['name']:i for i,n in enumerate(M.nodes)}
    M.parts[:]=[p for p in M.parts if not p['name'].startswith('hydraulic.coil') and p['name']not in('hydraulic.bottom_seat','hydraulic.spring_cup')]

    def pressed_cup(name,c,up,mat):
        # Closed annular stamping: a shallow dish, outer retention wall and
        # rolled lip, with a real center bore rather than a solid washer.
        c=np.array(c,float)
        profile=[(.018,-.009),(.047,-.009),(.062,-.005),(.068,.009),(.072,.012),(.073,.006),(.067,-.013),(.047,-.015),(.018,-.015),(.018,-.009)]
        rows=[]
        for a in np.linspace(0,math.tau,33):
            rows.append([c+[r*math.cos(a),up*y,r*math.sin(a)]for r,y in profile])
        M.grid(name,rows,mat,flip=up<0)

    for i in range(4):
        s=-1 if i%2==0 else 1;front=i<2
        b=np.array([s*(.55 if front else .56),.27 if front else .33,ctx['ZAXLE']if front else-ctx['ZAXLE']])
        length=.28 if front else .22
        with parent(ids[f'coil_{i}']):
            points=[]
            for t in np.linspace(0,1,145):
                u=max(0,min(1,(t-.035)/.930))
                points.append(b+[.049*math.cos(t*math.tau*6),length*u,.049*math.sin(t*math.tau*6)])
            tube('hydraulic.coil',points,.0085,red,8)
        seat=M.node(f'coil_{i}_seat',body,b,extras={'construction':'rigid pressed seat, independent of deforming coil','springCorner':i})
        with parent(seat):
            pressed_cup('hydraulic.bottom_seat',b,1,steel)
            torus('hydraulic.spring_isolator',b+[0,-.006,0],.049,.003,rubber,axis=(0,1,0),segments=28,sides=6)
        cup=np.array([b[0],.55,b[2]])
        with parent(ids[f'hydraulic_{i}_rod']):pressed_cup('hydraulic.spring_cup',cup,-1,chrome)

        center=np.array([s*(.765 if front else .755),ctx['HUB'],b[2]])
        with parent(ids[f'wheel_{i}_steer']):
            # The visible drum front is stepped into a hub flange; the rear
            # pressed backing plate, retaining bolts and grease cap are separate.
            cylinder('wheel.brake_backplate',center+[-s*.112,0,0],center+[-s*.102,0,0],.133,steel,40)
            torus('wheel.brake_backplate_step',center+[-s*.113,0,0],.108,.0035,steel,axis=(1,0,0),segments=36,sides=6)
            for a in np.linspace(0,math.tau,4,endpoint=False):
                p=center+[-s*.116,.092*math.sin(a),.092*math.cos(a)]
                cylinder('wheel.backplate_fastener',p,p+[-s*.007,0,0],.007,zinc,6)
        brake_spin=M.node(f'brake_{i}_spin',ids[f'wheel_{i}_steer'],center,extras={'construction':'rotating drum and hub, separate from removable wheel'})
        for p in M.parts:
            if p['parent']==ids[f'wheel_{i}_steer']and p['name']=='wheel.brake_drum':p['parent']=brake_spin
        with parent(brake_spin):
            torus('wheel.brake_drum_lip',center+[-s*.004,0,0],.123,.003,steel,axis=(1,0,0),segments=40,sides=6)
            cylinder('wheel.brake_hub_flange',center+[-s*.008,0,0],center+[s*.004,0,0],.079,zinc,32)
            cylinder('wheel.brake_hub',center+[s*.003,0,0],center+[s*.018,0,0],.034,steel,28)
            cylinder('wheel.grease_cap',center+[s*.017,0,0],center+[s*.033,0,0],.025,zinc,24,r2=.020)
            for a in np.linspace(0,math.tau,5,endpoint=False):
                p=center+[0,.0605*math.sin(a),.0605*math.cos(a)]
                cylinder('wheel.wheel_stud',p+[s*.002,0,0],p+[s*.024,0,0],.0055,zinc,10)
                cylinder('wheel.stud_shoulder',p+[-s*.001,0,0],p+[s*.006,0,0],.009,steel,12)


def refine_ram_mounts(ctx,coat,zinc):
    """Open reinforced frame towers, with actual fixed spherical top pins."""
    M,g,parent=ctx['M'],ctx['g'],ctx['parent'];body=ctx['body'];Z=ctx['ZAXLE']
    cylinder,torus=ctx['cylinder'],ctx['torus'];chrome=ctx['chrome'];box=g.box
    ids={n['name']:i for i,n in enumerate(M.nodes)}
    M.parts[:]=[p for p in M.parts if p['name']not in('chassis.ram_tower','chassis.ram_mount','hydraulic.top_pin','hydraulic.barrel','hydraulic.seal_collar')]
    rail=np.array([[.57,.27,2.39],[.57,.27,1.53],[.22,.25,.40],[.12,.25,-.20],[.52,.29,-1.46],[.58,.32,-2.30]])
    def member(name,a,b,w=.040,d=.040):
        a,b=np.array(a,float),np.array(b,float);axis=b-a
        length=np.linalg.norm(axis);B=g.basis(axis);center=(a+b)*.5
        # Formed, tapered closed sections replace the square cage bars.
        # The end lands retain their original envelope and engagement. The
        # waist removes material only, never entering a new moving clearance.
        outline=np.array([[-.30,-.50],[.30,-.50],[.50,-.30],[.50,.30],
            [.30,.50],[-.30,.50],[-.50,.30],[-.50,-.30],[-.30,-.50]])
        rows=[]
        for t in np.linspace(0,1,9):
            waist=.70+.30*abs(2*t-1)**1.4
            rows.append([center+B@np.array([x*w*waist,(t-.5)*(length+.008),z*d*waist])for x,z in outline])
        M.grid(name,rows,coat)
        for end,row in enumerate((rows[0][:-1],rows[-1][:-1])):
            vertices=np.asarray(row);faces=[(0,k,k+1)for k in range(1,len(row)-1)]
            normal=(-1 if end==0 else 1)*B[:,1]
            M.mesh(name,vertices,faces,coat,normals=np.tile(normal,(len(vertices),1)))
    for i in range(4):
        s=-1 if i%2==0 else 1;front=i<2;z=Z if front else-Z
        top=np.array([s*(.55 if front else.56),.86,z])
        postzs=[z-.28,z+.28]if front else[z-.28,z-.375]
        with parent(body):
            for pz in postzs:
                rx=np.interp(pz,rail[::-1,2],rail[::-1,0]);ry=np.interp(pz,rail[::-1,2],rail[::-1,1])
                foot=np.array([s*.49,ry+.045,pz]);head=np.array([s*.49,.825,pz])
                member('chassis.ram_rail_foot',[s*(rx-.042),ry+.035,pz],foot,.070,.055)
                member('chassis.ram_tower_post',foot,head)
                # Both front legs straddle the arm sweep. Rear legs stay aft
                # of the rear seat, carrying a short cantilevered head ring.
                hz=z+(math.copysign(.075,pz-z)if front else-.075)
                member('chassis.ram_header_riser',head,[s*.49,.844,hz],.035,.035)
                # A broad welded shoe wraps the rail web, with visible bolts.
                box('chassis.ram_rail_gusset',(s*(rx-.045),ry+.005,pz),(.012,.100,.090),coat,.003)
                for dz in(-.034,.034):
                    cylinder('chassis.ram_foot_bolt',(s*(rx-.057),ry+.005,pz+dz),(s*(rx-.035),ry+.005,pz+dz),.008,zinc,6)
            for hz in(z-.075,z+.075):
                member('chassis.ram_header_crossbar',[top[0]-.067,.844,hz],[top[0]+.067,.844,hz],.025,.025)
            for dx in(-.055,.055):
                member('chassis.ram_header_side',[top[0]+dx,.844,z-.075],[top[0]+dx,.844,z+.075],.025,.025)
                box('chassis.ram_pin_ear',top+[dx,-.004,0],(.008,.054,.060),coat,.003)
            # A fixed transverse pin and inner ball remain on the frame.
            # The cylinder's outer eye articulates around that same center.
            cylinder('hydraulic.ram_fixed_pin',top+[-.064,0,0],top+[.064,0,0],.0055,zinc,12)
            for dx in(-.066,.066):
                cylinder('hydraulic.ram_pin_head',top+[dx-.004,0,0],top+[dx+.004,0,0],.010,zinc,6)
            rows=[]
            for theta in np.linspace(math.asin(.006/.015),math.pi-math.asin(.006/.015),7):
                rows.append([top+[.015*math.cos(theta),.015*math.sin(theta)*math.cos(a),.015*math.sin(theta)*math.sin(a)]for a in np.linspace(0,math.tau,17)])
            M.grid('hydraulic.ram_spherical_inner_ball',rows,zinc)
            for sign in(-1,1):
                cylinder('hydraulic.ram_pin_spacer',top+[sign*.014,0,0],top+[sign*.049,0,0],.007,zinc,12,r2=.011)
        with parent(ids[f'hydraulic_{i}_barrel']):
            # Nominal top-to-gland distance remains245mm. The actual shell
            # begins30mm below the spherical pivot and is215mm long.
            cylinder('hydraulic.barrel',top+[0,-.030,0],top+[0,-.245,0],.0206375,chrome,24)
            for dy in(-.042,-.233):
                cylinder('hydraulic.seal_collar',top+[0,dy+.008,0],top+[0,dy-.008,0],.025,zinc,24)
            torus('hydraulic.ram_outer_race',top,.017,.006,zinc,axis=(1,0,0),segments=20,sides=6)
            cylinder('hydraulic.ram_eye_neck',top+[0,-.017,0],top+[0,-.038,0],.010,zinc,12)
        M.joints[f'hydraulic_{i}'].update(casingStartDistance=.030,casingShellLength=.215,
            fixedPinAxis=[1,0,0],frameTowerPosts=[[s*.49,float(pz)]for pz in postzs])


def route_exhaust_below_frame(ctx):
    """A local formed pipe drop clears the rear outrigger and its floor boot."""
    M,parent,tube=ctx['M'],ctx['parent'],ctx['tube']
    M.parts[:]=[p for p in M.parts if not p['name'].startswith('driveline.exhaust')]
    # Take off from the same manifold between the wishbone branches; the old
    # Z1.40 collector intersected the rear upper-arm branch and bush sleeve.
    for part in M.parts:
        if part['name']=='engine.exhaust_collector':part['p'][:,2]+=.14
    # Keep the manifold and external tailpipe endpoints. Descend
    # beside the oil pan, then pass below the frame waist and rear outrigger.
    # The nominal pipe lower surface remains113mm above the ground datum.
    zs=np.r_[.50,-.52,np.linspace(-.52,-.70,8)[1:],-1.21]
    with parent(ctx['body']):
        for sign in(-1,1):
            points=[]
            for t in np.linspace(0,1,8):
                points.append((sign*(.22+.03*t*t*(3-2*t)),.38-.14*t,1.54))
            points.append((sign*.25,.195,1.54))
            for angle in np.linspace(0,math.pi/2,9)[1:]:
                points.append((sign*.25,.195-.060*math.sin(angle),1.48+.060*math.cos(angle)))
            for t in np.linspace(0,1,9)[1:]:
                points.append((sign*(.25-.05*t*t*(3-2*t)),.135,1.48-.16*t))
            points.append((sign*.20,.135,1.08))
            for z in zs:
                if z<=-.70:drop=0
                elif z>=-.52:drop=1
                else:drop=.5+.5*math.cos(math.pi*(-.52-z)/.18)
                x=.32+(.50-z)*(.02/1.71)
                points.append((sign*x,.22-.085*drop,z))
            points.append((sign*.46,.23,-2.47))
            tube('driveline.exhaust',points,.022,ctx['silver'],12)


def form_frame_enclosures(ctx):
    """Cut real passages and form a closed skin around the rear frame route.

    The casings are the exposed boundary of joined convex volumes. Internal
    overlap faces are removed, including where a casing opens into the existing
    ram pocket. Thus neither a trunk skin nor a decorative end cap crosses steel.
    """
    from catrina_frame_pockets import frame_members,member_basis
    M,parent=ctx['M'],ctx['parent'];body=ctx['body']
    liner=next(i for i,m in enumerate(M.materials)if m['name'].endswith('plum_trunk_lining'))
    volumes=[];pockets=[];entries=[]

    def volume(center,half,B=np.eye(3),name='channel',material=liner):
        center,half,B=np.asarray(center,float),np.asarray(half,float),np.asarray(B,float)
        vertices=np.array([center+B@(half*np.array([x,y,z]))for x in(-1,1)for y in(-1,1)for z in(-1,1)])
        planes=[(sign*B[:,axis],float(sign*B[:,axis]@center+half[axis]))for axis in range(3)for sign in(-1,1)]
        return dict(center=center,half=half,B=B,planes=planes,lo=vertices.min(0),hi=vertices.max(0),name=name,mat=material)

    for side in(-1,1):
        for name,a,b,width,height in frame_members():
            if name=='original_center'and abs(b[2]+.45)<1e-6:
                # The wider retained rail enters the narrow outrigger boot.
                # Its real cross-section needs an open entry collar, not an
                # end wall through the rail. A3mm assembly seam stays clear
                # of the original bevel and carries no suspension motion.
                aa=a*[side,1,1];bb=b*[side,1,1]
                entries.append(volume((aa+bb)/2,[width/2+.003,np.linalg.norm(bb-aa)/2+.015,height/2+.003],member_basis(aa,bb),name='retained_rail_entry'))
            if name not in('rear_outrigger','rear_underfloor','rear_riser','rear_header','rear_pocket','rear_post_bridge'):continue
            a=a*[side,1,1];b=b*[side,1,1];B=member_basis(a,b)
            if name=='rear_pocket':
                # A closed shallow bridge leaves the Panhard sweep below it;
                # the main service floor remains continuous underneath.
                lo=np.minimum(a,b)-[width/2+.012,height/2+.012,.024]
                hi=np.maximum(a,b)+[width/2+.012,height/2+.012,.024]
                volumes.append(volume((lo+hi)/2,(hi-lo)/2,name='raised_channel'))
            else:
                # The tighter cabin/tire corridor uses a6mm steel-to-skin
                # offset; member ends extend5mm, inside the12mm casing ends.
                volumes.append(volume((a+b)/2,[width/2+.006,np.linalg.norm(b-a)/2+.012,height/2+.006],B,
                    name='carpeted_boot'if name in('rear_outrigger','rear_underfloor','rear_riser')else'header_return',
                    material=ctx['plum']if name in('rear_outrigger','rear_underfloor','rear_riser')else liner))
        # Existing pockets already close this region; their roof remains above
        # the new header and the upright posts. These are union voids, not cuts
        # into the exterior quarter or the safe outer wheelhouse crown.
        lo=np.array([side*.345,.594,-ctx['ZAXLE']-.415]);hi=np.array([side*.661,.866,-ctx['ZAXLE']+.170])
        x0,x1=sorted((lo[0],hi[0]));lo[0]=x0;hi[0]=x1
        pockets.append(volume((lo+hi)/2,(hi-lo)/2,name='existing_ram_pocket'))

    def split(poly,normal,limit):
        distance=poly[:,:3]@normal-limit
        if np.all(distance<=1e-10):return poly,None
        if np.all(distance>=-1e-10):return None,poly
        inside=[];outside=[]
        for i,a in enumerate(poly):
            b=poly[(i+1)%len(poly)];da=distance[i];db=distance[(i+1)%len(poly)]
            (inside if da<=0 else outside).append(a)
            if (da<0<db)or(db<0<da):
                q=a+(b-a)*(da/(da-db));inside.append(q);outside.append(q)
        return (np.array(inside)if len(inside)>=3 else None,np.array(outside)if len(outside)>=3 else None)

    def subtract(poly,vol):
        if np.any(poly[:,:3].max(0)<vol['lo']-1e-9)or np.any(poly[:,:3].min(0)>vol['hi']+1e-9):return [poly]
        remaining=poly;outside=[]
        for normal,limit in vol['planes']:
            remaining,fragment=split(remaining,normal,limit)
            if fragment is not None:outside.append(fragment)
            if remaining is None:break
        return outside

    def clipped(polygons,cutters):
        for v in cutters:
            polygons=[q for p in polygons for q in subtract(p,v)]
            if not polygons:break
        return polygons

    def emit(name,polygons,material,twosided=False):
        vertices=[];normals=[];uv=[];faces=[]
        for polygon in polygons:
            n0=len(vertices);vertices.extend(polygon[:,:3]);normals.extend(polygon[:,3:6]);uv.extend(polygon[:,6:8])
            faces.extend((n0,n0+k,n0+k+1)for k in range(1,len(polygon)-1))
        if not faces:return
        vertices=np.asarray(vertices);normals=np.asarray(normals);faces=np.asarray(faces)
        M.mesh(name,vertices,faces,material,np.asarray(uv),normals)
        if twosided:M.mesh(name,vertices,faces[:,::-1],material,np.asarray(uv),-normals)

    targets=('body.cabin_floor','interior.floor_carpet','body.rear_bulkhead','body.trunk_front_bulkhead',
        'body.trunk_center_floor','body.trunk_wheelhouse','body.trunk_ram_inner_wall',
        'body.trunk_ram_return','body.trunk_ram_cover','body.trunk_ram_post_sleeve')
    original=M.parts[:];M.parts=[]
    with parent(body):
        for part in original:
            if part['parent']!=body or not any(part['name']==t or part['name'].startswith(t+'.')for t in targets):
                M.parts.append(part);continue
            world=part['p']+M.origins[body]
            nearby=[v for v in volumes if np.all(world.max(0)>=v['lo'])and np.all(world.min(0)<=v['hi'])]
            if not nearby:M.parts.append(part);continue
            data=np.c_[world,part['n'],part['uv']]
            emit(part['name'],clipped([data[f]for f in part['f']],nearby),part['mat'])
        for i,v in enumerate(volumes):
            polygons=[]
            for axis in range(3):
                others=[j for j in range(3)if j!=axis]
                for sign in(-1,1):
                    corners=[];normal=sign*v['B'][:,axis]
                    for u,w in((-1,-1),(1,-1),(1,1),(-1,1)):
                        q=np.zeros(3);q[axis]=sign*v['half'][axis];q[others]=np.array([u,w])*v['half'][others]
                        p=v['center']+v['B']@q
                        corners.append(np.r_[p,normal,[(p[0]+1)/2,(3-p[2])/6]])
                    corners=np.array(corners)
                    if np.dot(np.cross(corners[1,:3]-corners[0,:3],corners[2,:3]-corners[0,:3]),normal)<0:corners=corners[::-1]
                    polygons.append(corners)
            exposed=[]
            for polygon in polygons:
                normal=polygon[0,3:6];cutters=[]
                for j,w in enumerate(volumes):
                    if i==j:continue
                    # Adjacent casings can share an outer plane. Preserve one
                    # copy of the common patch; symmetric subtraction would
                    # otherwise punch a hole through both coincident skins.
                    same_outer=any(np.dot(normal,n)>1-1e-8 and np.max(np.abs(polygon[:,:3]@n-d))<1e-8 for n,d in w['planes'])
                    if same_outer and i<j:continue
                    cutters.append(w)
                exposed.extend(clipped([polygon],cutters+pockets+entries))
            emit('body.trunk_frame_channel_'+v['name'],exposed,v['mat'],twosided=True)
    ctx['frame_enclosure_scope']={
        'mainFloorY':[.594,.626], 'highRailCenterY':.770,'highChannelRoofY':.837,
        'mainRailAbsX':.270,'mainChannelOuterAbsX':[.2105,.3295],'highChannelBottomY':.703,
        'outboardRailAbsX':.795,'tightCasingSteelOffset':.006,
        'construction':'Unioned closed formed skins with real floor, bulkhead and ram-pocket openings'}


def reinforce_lid_inners(ctx):
    """Shallow formed webs on the existing inner skins, under their hinges."""
    from scipy.interpolate import LinearNDInterpolator
    M,parent=ctx['M'],ctx['parent'];rose=ctx['rose']
    # Both trunk hinge assemblies move along their existing common X axis.
    # This clears the ram heads without changing the Y/Z pivot or opening arc.
    for part in M.parts:
        if part['name'].startswith('body.trunk_hinge_'):
            part['p'][:,0]-=math.copysign(.24,float(part['p'][:,0].mean()))
    for front in(True,False):
        name='hood'if front else'trunk';skin=next(p for p in M.parts if p['name']=='body.'+name)
        vertices=skin['p']+M.origins[skin['parent']];z0,z1=vertices[:,2].min(),vertices[:,2].max()
        inner=next(p for p in M.parts if p['name']=='body.'+name+'_inner')
        iv=inner['p']+M.origins[inner['parent']]
        inner_y=LinearNDInterpolator(iv[:,[0,2]],iv[:,1])
        # Stay away from the rolled end and hinge/cowl; preserve the perimeter
        # flange and its actual contour. No new low projection over equipment.
        za,zb=z0+.22,z1-.22
        with parent(skin['parent']):
            for sign in(-1,1):
                rows=[]
                for t in np.linspace(0,1,25):
                    z=za+(zb-za)*t;x=sign*(.36+.11*math.sin(t*math.pi))
                    fade=min(1,t/.08,(1-t)/.08)
                    profile=[(-.025,.001),(-.017,.001-.006*fade),(.017,.001-.006*fade),(.025,.001)]
                    rows.append([(x+dx,float(inner_y(x+dx,z))+dy,z)for dx,dy in profile])
                M.grid('body.'+name+'_pressed_reinforcement',rows,rose,flip=True)
            for t in(.28,.72):
                z=za+(zb-za)*t;rows=[];half=.36+.11*math.sin(t*math.pi)-.025
                for x in np.linspace(-half,half,25):
                    fade=min(1,(x+half)/.08,(half-x)/.08)
                    rows.append([(x,float(inner_y(x,z+dz))+dy,z+dz)for dz,dy in[(-.018,.001),(-.010,.001-.006*fade),(.010,.001-.006*fade),(.018,.001)]])
                M.grid('body.'+name+'_pressed_reinforcement',rows,rose)


def refine_slip_driveshaft(ctx,zinc):
    """Fixed-length tube and translating splined member, with no metal scale."""
    M,g,parent=ctx['M'],ctx['g'],ctx['parent'];cylinder=ctx['cylinder'];steel=ctx['steel']
    node=next(i for i,n in enumerate(M.nodes)if n['name']=='driveshaft')
    a=np.array(M.joints['driveshaft']['a']);b=np.array(M.joints['driveshaft']['b']);length=np.linalg.norm(b-a)
    M.parts[:]=[p for p in M.parts if p['parent']!=node]
    M.nodes[node]['rotation']=Rotation.from_matrix(g.basis(b-a)).as_quat().tolist()
    with parent(node):
        cylinder('driveline.rigid_tube',a+[0,.075,0],a+[0,1.600,0],.034,steel,24)
        cylinder('driveline.slip_mouth',a+[0,1.575,0],a+[0,1.610,0],.039,zinc,20)
        cylinder('driveline.front_yoke',a+[0,.012,0],a+[0,.075,0],.043,zinc,20)
        cylinder('driveline.front_universal_cross',a+[-.050,.016,0],a+[.050,.016,0],.012,zinc,14)
    M.node('driveshaft_front_joint',node,a)
    M.node('driveshaft_tube_end',node,a+[0,1.600,0])
    slip_origin=a+[0,length,0]
    slip=M.node('driveshaft_slip',node,slip_origin,extras={'rigidLength':.550,'construction':'rigid splined slip member; translation only'})
    with parent(slip):
        cylinder('driveline.rigid_slip_member',slip_origin+[0,-.550,0],slip_origin+[0,-.060,0],.023,zinc,20)
        for theta in np.linspace(0,math.tau,12,endpoint=False):
            offset=np.array([.023*math.cos(theta),0,.023*math.sin(theta)])
            cylinder('driveline.slip_spline',slip_origin+offset+[0,-.540,0],slip_origin+offset+[0,-.072,0],.0013,zinc,6)
        cylinder('driveline.rear_yoke',slip_origin+[0,-.060,0],slip_origin,.038,zinc,20)
        cylinder('driveline.rear_universal_cross',slip_origin+[-.046,-.014,0],slip_origin+[.046,-.014,0],.011,zinc,14)
    M.node('driveshaft_rear_joint',slip,slip_origin)
    M.node('driveshaft_slip_tip',slip,slip_origin+[0,-.550,0])
    M.joints['driveshaft'].update(outerTubeEnd=1.600,slipMemberLength=.550,fixedMetalScale=[1,1,1])
