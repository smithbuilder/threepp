"""Original rear-engine packaging for the fictional Cinder Safari.

Separate serviceable engine protection, chassis cradle, rubber-isolated
transverse silencer and open exhaust plumbing. Coordinates are chassis metres.
This is visual mechanical plausibility, not a certified automotive design.
"""
import math
import numpy as np
from scipy.interpolate import CubicSpline

TAU=math.tau


def build_rear_assembly(model, primitives, materials):
    box=primitives['box'];raw_cylinder=primitives['cylinder'];torus=primitives['torus']
    ellipsoid=primitives['ellipsoid'];raw_polyline=primitives['polyline'];plate=primitives['plate']
    frame=materials['frame'];alloy=materials['alloy'];steel=materials['steel']
    cast=materials['cast'];rubber=materials['rubber'];soot=materials['soot'];weld=materials['weld']
    first=len(model.parts)
    # These records come from the same paths passed to the mesh builders.
    # They are exported for CPU clearance regression, never a second model.
    hot_paths=[];cold_paths=[];collector_surfaces=[];rear_outlet_azimuths={}

    def cylinder(name,a,b,radius,material,segments=12):
        raw_cylinder(name,a,b,radius,material,segments)
        if name.startswith(('rear.frame.','rear.bumper.')):
            cold_paths.append(dict(name=name,points=np.asarray([a,b]).tolist(),radius=radius))

    def polyline(name,points,radius,material,segments=12):
        raw_polyline(name,points,radius,material,segments)
        if name.startswith(('rear.frame.','rear.bumper.')):
            cold_paths.append(dict(name=name,points=np.asarray(points).tolist(),radius=radius))

    def smooth(points,spacing=.025):
        points=np.asarray(points,float)
        distances=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        if len(points)<3:return points
        first=(points[1]-points[0])/np.linalg.norm(points[1]-points[0])
        last=(points[-1]-points[-2])/np.linalg.norm(points[-1]-points[-2])
        spline=CubicSpline(distances,points,axis=0,bc_type=((1,first),(1,last)))
        return spline(np.linspace(0,distances[-1],max(len(points),int(math.ceil(distances[-1]/spacing))+1)))

    def fillet_open(points):
        points=np.asarray(points,float);result=[points[0]]
        for i in range(1,len(points)-1):
            c=points[i];a=c+(points[i-1]-c)*.22;b=c+(points[i+1]-c)*.22
            result.extend((1-t)**2*a+2*t*(1-t)*c+t*t*b for t in np.linspace(0,1,8))
        return np.asarray(result+[points[-1]])

    def frames(points,first=None,last=None):
        tangent=np.gradient(points,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
        if first is not None:tangent[0]=first/np.linalg.norm(first)
        if last is not None:tangent[-1]=last/np.linalg.norm(last)
        normal=primitives['basis'](tangent[0])[:,0];result=[]
        for i in range(len(points)):
            if i:
                axis=np.cross(tangent[i-1],tangent[i]);length=np.linalg.norm(axis)
                if length>1e-9:
                    axis/=length;angle=math.atan2(length,float(tangent[i-1]@tangent[i]))
                    normal=normal*math.cos(angle)+np.cross(axis,normal)*math.sin(angle)+axis*(axis@normal)*(1-math.cos(angle))
                normal-=tangent[i]*(normal@tangent[i]);normal/=max(np.linalg.norm(normal),1e-9)
            result.append((normal.copy(),np.cross(tangent[i],normal),tangent[i]))
        return result

    def pipe(name,control,outer=.024,wall=.0015,segments=16,rolled=False,azimuth=None):
        """Two actual walls plus annular ends; never a disk closing the bore."""
        control=np.asarray(control,float)
        points=smooth(control);orient=frames(points,control[1]-control[0],control[-1]-control[-2]);uv=[];outer_p=[];inner_p=[]
        hot_paths.append(dict(name=name,points=points.tolist(),radius=outer,wall=wall))
        angles=np.linspace(0,TAU,segments+1) if azimuth is None else np.asarray(azimuth,float)
        segments=len(angles)-1
        for i,(point,(normal,binormal,_)) in enumerate(zip(points,orient)):
            for j,a in enumerate(angles):
                radial=normal*math.cos(a)+binormal*math.sin(a)
                outer_p.append(point+outer*radial);inner_p.append(point+(outer-wall)*radial);uv.append((j/segments,i/max(1,len(points)-1)))
        faces=[]
        for i in range(len(points)-1):
            for j in range(segments):
                a=i*(segments+1)+j;b=a+1;c=a+segments+1;d=c+1;faces.extend([(a,b,c),(b,d,c)])
        model.mesh(name+'.outer_wall',outer_p,faces,steel,uv)
        model.mesh(name+'.sooted_inner_wall',inner_p,[tuple(reversed(f)) for f in faces],soot,uv)
        for end in [0,len(points)-1]:
            start=end*(segments+1);p=np.r_[np.asarray(outer_p[start:start+segments+1]),np.asarray(inner_p[start:start+segments+1])];f=[]
            for j in range(segments):
                a=j;b=j+1;c=j+segments+1;d=c+1
                f.extend([(a,c,b),(b,c,d)] if end==0 else [(a,b,c),(b,d,c)])
            model.mesh(name+('.start_annular_wall' if end==0 else '.mouth_annular_wall'),p,f,steel)
        if rolled:
            torus(name+'.rolled_mouth_lip',points[-1],outer-wall*.5,wall*.70,steel,orient[-1][2],40,8)
        return points

    def merge_collector(side):
        """A hollow three-port entry plate and reducing pressure case.

        Each primary ends at its own open bore. Unlike overlapping capped
        cylinders, no primary wall continues across another gas passage.
        Three convex sectors share exact radial boundaries in the entry
        plate, so the holes do not rely on deleting triangle centroids.
        """
        center=np.array([side*.66,.495,-1.985]);outer=.064;wall=.002
        holes=[]
        for j,angle in enumerate([math.radians(210),math.radians(330),math.radians(90)]):
            hole=center+np.array([side*.0338*math.cos(angle),.0338*math.sin(angle),0])
            holes.append(hole)
            arc=np.linspace(angle-math.pi/3,angle+math.pi/3,7)
            boundary=np.array([[0.,0.]]+[[side*outer*math.cos(a),outer*math.sin(a)] for a in arc])
            boundary-=hole[:2]-center[:2]
            angles=np.unique(np.round(np.r_[np.arange(16)*TAU/16,
                np.mod(np.arctan2(boundary[:,1],boundary[:,0]),TAU)],12))
            outer_loop=[]
            for a in angles:
                ray=np.array([math.cos(a),math.sin(a)]);hits=[]
                for q,r in zip(boundary,np.roll(boundary,-1,axis=0)):
                    edge=r-q;system=np.c_[ray,-edge]
                    if abs(np.linalg.det(system))<1e-12:continue
                    distance,t=np.linalg.solve(system,q)
                    if distance>0 and -1e-9<=t<=1+1e-9:hits.append(distance)
                outer_loop.append(ray*min(hits))
            outer_loop=np.asarray(outer_loop)
            radial=np.c_[np.cos(angles),np.sin(angles)]
            n=len(angles)
            for face_side in [-1,1]:
                p=np.array([hole+[q[0],q[1],face_side*wall/2]
                    for loop in [outer_loop,radial*.024] for q in loop])
                f=[]
                for k in range(n):
                    k1=(k+1)%n;f.extend([(k,k1,n+k),(k1,n+k1,n+k)])
                if face_side<0:f=[tuple(reversed(v)) for v in f]
                model.mesh(f'rear.exhaust.merge_collector.{side}.entry_cell.{j}.{face_side}',p,f,steel)
            bore_p=np.array([hole+[q[0],q[1],z] for z in [-wall/2,wall/2] for q in radial*.024])
            bore_f=[]
            for k in range(n):
                k1=(k+1)%n;bore_f.extend([(k,n+k,k1),(k1,n+k,n+k1)])
            model.mesh(f'rear.exhaust.merge_collector.{side}.open_inlet_wall.{j}',bore_p,bore_f,soot)
            torus(f'rear.exhaust.merge_collector.{side}.inlet_weld.{j}',hole,
                  .024,.0015,weld,(0,0,1),24,6)
        # Smooth concentric taper; both case skins remain open at the exit.
        outlet=.044 if side<0 else .045
        stations=[(-1.985,.064),(-2.015,.060),(-2.05,outlet+.004),(-2.075,outlet)]
        for inside in [False,True]:
            rows=[[(center[0]+(radius-(wall if inside else 0))*math.cos(a),
                    center[1]+(radius-(wall if inside else 0))*math.sin(a),z)
                    for a in np.linspace(0,TAU,33)] for z,radius in stations]
            model.grid(f'rear.exhaust.merge_collector.{side}.{"inside" if inside else "outside"}',rows,soot if inside else steel,flip=inside)
        rear=np.array([center[0],center[1],stations[-1][0]])
        # Only annular exit material, never a pressure-blocking disk.
        rows=[[(rear[0]+r*math.cos(a),rear[1]+r*math.sin(a),rear[2])
            for a in np.linspace(0,TAU,33)] for r in [outlet-wall,outlet]]
        model.grid(f'rear.exhaust.merge_collector.{side}.open_exit_annulus',rows,steel)
        hot_paths.append(dict(name=f'rear.exhaust.merge_collector.{side}',
            points=[center.tolist(),rear.tolist()],radius=outer,wall=wall,
            envelope='conservative maximum-radius capsule of taper'))
        torus(f'rear.exhaust.merge_collector.{side}.entry_plate_perimeter_weld',
              center,.0639,.002,weld,(0,0,1),48,6)
        collector_surfaces.append(dict(name=f'rear.exhaust.merge_collector.{side}',
            center=center.tolist(),stations=[dict(z=z,radius=r) for z,r in stations],
            inletCenters=[h.tolist() for h in holes],inletRadius=.024,wall=wall))
        return holes,rear

    # The transverse member meets the existing fixed hinge pins at x +/-.70.
    cylinder('rear.frame.hinge_crossmember',(-.72,.36,-.30),(.72,.36,-.30),.034,frame,12)
    for side in [-1,1]:
        x=side*.60
        polyline(f'rear.frame.longitudinal_rail.{side}',[(x,.36,-.30),(x,.38,-.55),(x,.38,-2.17)],.033,frame,12)
        box(f'rear.frame.hinge_splice_plate.{side}',(side*.705,.36,-.30),(.12,.10,.14),frame,.012,3)
        for z in [-.34,-.26]:cylinder(f'rear.frame.hinge_splice_bolt.{side}.{z}',(side*.705,.305,z),(side*.705,.415,z),.013,alloy,6)
        # A separate engine cradle begins behind the closed cabin bulkhead.
        # The former upper rails crossed that panel. New lateral outriggers
        # meet the untouched lower rails, leaving the live shock anchors alone.
        cylinder(f'rear.frame.upper_side_rail.{side}',(side*.80,.72,-1.62),(side*.80,.72,-2.44),.028,frame,12)
        cylinder(f'rear.frame.front_bottom_outrigger.{side}',(x,.38,-1.62),(side*.80,.38,-1.62),.026,frame,10)
        cylinder(f'rear.frame.outer_bottom_side_rail.{side}',(side*.80,.38,-1.62),(side*.80,.38,-2.05),.026,frame,10)
        cylinder(f'rear.frame.vertical_engine_support.{side}.-1.62',(side*.80,.38,-1.62),(side*.80,.72,-1.62),.026,frame,10)
        cylinder(f'rear.frame.forward_triangle.{side}',(side*.80,.38,-1.86),(side*.80,.72,-1.62),.026,frame,10)
        cylinder(f'rear.frame.rear_bottom_outrigger.{side}',(x,.38,-2.05),(side*.80,.38,-2.05),.024,frame,10)
        cylinder(f'rear.frame.vertical_engine_support.{side}.-2.05',(side*.80,.38,-2.05),(side*.80,.72,-2.05),.026,frame,10)
        cylinder(f'rear.frame.rear_triangle.{side}',(side*.80,.38,-2.05),(side*.80,.72,-1.72),.026,frame,10)
        for z in [-1.66,-1.86]:
            plate(f'rear.frame.welded_gusset.{side}.{z}',[(x,.38,z-.065),(x,.38,z+.065),(side*.405,.515,z)],frame)
            cylinder(f'rear.frame.engine_mount_riser.{side}.{z}',(x,.38,z),(side*.405,.535,z),.020,frame,10)
            box(f'rear.frame.engine_mount_shelf.{side}.{z}',(side*.405,.535,z),(.18,.025,.13),frame,.008,3)
            ellipsoid(f'rear.engine.rubber_mount.{side}.{z}',(side*.405,.575,z),(.052,.028,.043),rubber,16,8)
            box(f'rear.engine.cast_mount_foot.{side}.{z}',(side*.355,.614,z),(.15,.035,.10),cast,.009,3)
            cylinder(f'rear.engine.mount_stud.{side}.{z}',(side*.405,.525,z),(side*.405,.650,z),.010,alloy,8)
            cylinder(f'rear.engine.mount_hex_nut.{side}.{z}',(side*.405,.632,z),(side*.405,.644,z),.014,alloy,6)
    # No upper crossmember is permitted inside the cast crankcase. The last
    # lower crossbar is ahead of the silencer, rather than touching its case.
    for z,y,w in [(-.55,.38,.60),(-1.06,.38,.60),(-1.86,.38,.60),(-2.44,.72,.80)]:
        cylinder(f'rear.frame.crossmember.{z}.{y}',(-w,y,z),(w,y,z),.029,frame,12)

    # Rear engine: crankcase, sump, opposing heads and six separate port stubs.
    block_first=len(model.parts)
    box('rear.engine.cast_crankcase',(0,.78,-1.84),(.61,.37,.54),cast,.065,6)
    # A cast lower-rear relief keeps the pressure case out of the silencer.
    # The front stays behind the cabin bulkhead. The Z map is monotonic at
    # every height; its analytic Jacobian also transforms the surface normals.
    for part in model.parts[block_first:]:
        p=part['p'].astype(float);normal=part['n'].astype(float)
        t=np.clip((p[:,1]-.595)/.105,0,1)
        blend=t*t*(3-2*t);scale=(.39+.14*blend)/.54
        derivative=(.14/.54)*6*t*(1-t)/.105
        dz_dy=(p[:,2]+1.57)*derivative
        normal[:,1]-=dz_dy*normal[:,2]/scale
        normal[:,2]/=scale
        normal/=np.linalg.norm(normal,axis=1)[:,None]
        p[:,2]=-1.58+(p[:,2]+1.57)*scale
        part['p']=p.astype(np.float32);part['n']=normal.astype(np.float32)
    ellipsoid('rear.engine.lower_sump',(0,.55,-1.7675),(.275,.110,.1875),cast,32,14)
    for side in [-1,1]:
        box(f'rear.engine.cylinder_bank.{side}',(side*.345,.77,-1.84),(.20,.24,.52),cast,.033,4)
        for j,y in enumerate(np.linspace(.71,.87,7)):
            box(f'rear.engine.cooling_fin.{side}.{j}',(side*.355,y,-1.84),(.23,.009,.51),alloy,.004,2)
        entries,collector_exit=merge_collector(side)
        for j,z in enumerate([-1.63,-1.80,-1.97]):
            ellipsoid(f'rear.engine.cast_port_boss.{side}.{j}',(side*.430,.67,z),(.035,.046,.046),cast,16,10)
            torus(f'rear.engine.exhaust_port_flange.{side}.{j}',(side*.455,.67,z),.031,.006,cast,(1,0,0),24,6)
            for yy in [.638,.702]:cylinder(f'rear.engine.port_flange_bolt.{side}.{j}.{yy}',(side*.443,yy,z),(side*.469,yy,z),.007,alloy,6)
            entry=entries[j]
            if j==0:
                lane=[(side*.455,.67,z),(side*.515,.67,z),(side*.555,.58,-1.71),
                      (side*.585,.48,-1.83),(entry[0],entry[1],-1.95),entry]
            elif j==1:
                lane=[(side*.455,.67,z),(side*.515,.67,z),(side*.615,.60,-1.82),
                      (entry[0],.49,-1.90),(entry[0],entry[1],-1.95),entry]
            else:
                lane=[(side*.455,.67,z),(side*.515,.67,z),(side*.60,.63,-1.94),
                      (entry[0],.57,-1.93),(entry[0],entry[1],-1.955),entry]
            pipe(f'rear.exhaust.bank_header.{side}.{j}',lane,.024,.0015,12)
        # Each bank enters its own OPEN silencer end neck. The final straight
        # X tangent meets that neck coplanarly; there is no crossing crossover.
        elbow=[]
        for a in np.linspace(0,math.pi/2,9):
            t=a/(math.pi/2)
            elbow.append((side*(.575+.085*math.cos(a)),.495+.035*t*t*(3-2*t),
                          -2.105-.085*math.sin(a)))
        pipe(f'rear.exhaust.silencer_bank_inlet.{side}',
             [collector_exit,(side*.66,.495,-2.095)]+elbow+[(side*.56,.53,-2.19)],
             .044 if side<0 else .045,.002,20)

    # Closed pressure case with OPEN axial necks. Unlike a capped cylinder,
    # neither neck has an opaque disk hidden across the exhaust flow path.
    cy,cz=.53,-2.19
    profile=[(-.56,.044,.044),(-.55,.070,.090),(-.525,.102,.143),(-.49,.110,.155),(.49,.110,.155),(.525,.102,.143),(.55,.070,.090),(.56,.045,.045)]
    values=np.asarray(profile)
    # The two end tapers retain their open axial inlet necks.
    for side in [-1,1]:
        stations=np.unique(np.asarray([abs(q[0]) for q in profile if abs(q[0])>=.49]))*side
        stations.sort();p=[]
        for x in stations:
            ry=np.interp(x,values[:,0],values[:,1]);rz=np.interp(x,values[:,0],values[:,2])
            p.append([(x,cy+ry*math.cos(a),cz+rz*math.sin(a)) for a in np.linspace(0,TAU,33)])
        model.grid(f'rear.exhaust.silencer_axial_neck_and_endcap.{side}',p,steel,flip=True)
    p=[]
    for x in np.linspace(-.49,.49,21):
        ry=np.interp(x,values[:,0],values[:,1]);rz=np.interp(x,values[:,0],values[:,2])
        p.append([(x,cy+ry*math.cos(a),cz+rz*math.sin(a)) for a in np.linspace(0,math.pi,21)])
    model.grid('rear.exhaust.transverse_oval_silencer_case.front_half',p,steel,flip=True)
    # Author the rear case around two real outlet holes. Radial cells run from
    # each circular hole to exact rectangular half-case boundaries; the curved
    # ellipse is evaluated at every vertex. No pressure wall crosses a port.
    for side in [-1,1]:
        hx,hy=side*.13,.49;hole_r=.052
        x0,x1=(-.49,0) if side<0 else (0,.49)
        corners=np.array([[x0,cy-.11],[x1,cy-.11],[x1,cy+.11],[x0,cy+.11]])-[hx,hy]
        angles=np.unique(np.round(np.r_[np.arange(48)*TAU/48,
            np.mod(np.arctan2(corners[:,1],corners[:,0]),TAU)],12))
        rays=np.c_[np.cos(angles),np.sin(angles)]
        outer=[]
        for ray in rays:
            limits=[((x1-hx) if ray[0]>0 else (x0-hx))/ray[0] if abs(ray[0])>1e-12 else np.inf,
                    ((cy+.11-hy) if ray[1]>0 else (cy-.11-hy))/ray[1] if abs(ray[1])>1e-12 else np.inf]
            outer.append(ray*min(limits))
        rows=[];normals=[]
        def back_z(y):return cz-.155*math.sqrt(max(0,1-((y-cy)/.11)**2))
        for t in np.linspace(0,1,8):
            row=[];nr=[]
            for ray,q in zip(rays,outer):
                u,v=ray*hole_r*(1-t)+q*t;x,y=hx+u,hy+v;z=back_z(y)
                normal=np.array([0,(y-cy)/(.11**2),(z-cz)/(.155**2)])
                row.append((x,y,z));nr.append(normal/np.linalg.norm(normal))
            rows.append(row+[row[0]]);normals.append(nr+[nr[0]])
        n=len(angles)+1;f=[]
        for i in range(7):
            for j in range(n-1):
                a=i*n+j;b=a+1;c=a+n;d=c+1;f.extend([(a,b,c),(b,d,c)])
        model.mesh(f'rear.exhaust.transverse_oval_silencer_case.rear_port_cell.{side}',
            np.asarray(rows).reshape(-1,3),f,steel,normals=np.asarray(normals).reshape(-1,3))
        rear_outlet_azimuths[side]=np.r_[angles,angles[0]+TAU]
        # Two actual neck skins connect the curved case openings to planar,
        # axis-aligned outlet tubes. Their bores are open throughout.
        for inside in [False,True]:
            rr=hole_r-(.0035 if inside else 0)
            rings=[]
            for end in [False,True]:
                rings.append([(hx+rr*math.cos(a),hy+rr*math.sin(a),
                    -2.39 if end else back_z(hy+rr*math.sin(a))+(.002 if inside else 0))
                    for a in rear_outlet_azimuths[side]])
            model.grid(f'rear.exhaust.silencer_rear_outlet_neck.{side}.{"inner" if inside else "outer"}',rings,soot if inside else steel,flip=inside)
        hot_paths.append(dict(name=f'rear.exhaust.silencer_rear_outlet_neck.{side}',
            points=[[hx,hy,back_z(hy)],[hx,hy,-2.39]],radius=hole_r,wall=.0035))
    for side in [-1,1]:
        torus(f'rear.exhaust.silencer_endcap_weld.{side}',(side*.49,cy,cz),.13,.0025,weld,(1,0,0),40,6,stretch=(.110/.13,1,.155/.13))
    for side in [-1,1]:
        tail_angles=np.sort(np.mod(-rear_outlet_azimuths[side][:-1],TAU))
        tail_angles=np.r_[tail_angles,tail_angles[0]+TAU]
        pipe(f'rear.exhaust.twin_open_tailpipe.{side}',[(side*.13,.49,-2.39),(side*.13,.49,-2.555)],.052,.0035,28,True,
             azimuth=tail_angles)
        torus(f'rear.exhaust.tailpipe_clamp.{side}',(side*.13,.492,-2.52),.054,.003,alloy,(0,-.08,-1),28,6)

    # Independent stainless straps, hanging from rubber isolators on the cradle.
    for side in [-1,1]:
        x=side*.36;p=[]
        for xx in [x-.022,x+.022]:
            p.append([(xx,cy+.114*math.cos(a),cz+.159*math.sin(a)) for a in np.linspace(0,TAU,41)])
        model.grid(f'rear.exhaust.independent_clamp_band.{side}',p,alloy,flip=True)
        box(f'rear.exhaust.clamp_tensioner.{side}',(x,.652,-2.19),(.065,.020,.065),alloy,.005,3)
        cylinder(f'rear.exhaust.clamp_bolt.{side}',(x-.035,.658,-2.19),(x+.035,.658,-2.19),.006,weld,6)
        hx=side*.63
        polyline(f'rear.exhaust.lower_hanger_rod.{side}',[(x,.652,-2.19),(side*.58,.666,-2.25),(hx,.655,-2.26)],.007,steel,8)
        polyline(f'rear.exhaust.upper_hanger_chassis_bracket.{side}',[(side*.80,.72,-2.28),(side*.66,.72,-2.28),(hx,.700,-2.26)],.008,frame,8)
        for y in [.700,.655]:
            torus(f'rear.exhaust.rubber_isolator_eye.{side}.{y}',(hx,y,-2.26),.017,.007,rubber,(1,0,0),24,8)
            cylinder(f'rear.exhaust.hanger_peg.{side}.{y}',(hx-.018,y,-2.26),(hx+.018,y,-2.26),.007,steel,10)
        box(f'rear.exhaust.rubber_isolator_web.{side}',(hx,.6775,-2.26),(.014,.025,.014),rubber,.005,3)

    # Aluminized heat shield, independent from the hot case. Hangers now run
    # outside its edges. Its raised front fold clears the highest rear primary.
    xs=[-.58,-.405,-.325,.325,.405,.58];zs=[-2.37,-2.34,-2.205,-2.115,-2.06,-1.98]
    def shield_y(z):
        t=float(np.clip((z+2.115)/.135,0,1))
        return .695+.012*((z+2.19)/.21)**2+.023*t*t*(3-2*t)
    shield_ys=[shield_y(z) for z in zs]
    p=[(x,shield_y(z),z) for z in zs for x in xs];f=[]
    for iz in range(len(zs)-1):
        for ix in range(len(xs)-1):
            a=iz*len(xs)+ix;b=a+1;c=a+len(xs);d=c+1;f.extend([(a,c,b),(b,c,d)])
    model.mesh('rear.heat_shield.separate_shaped_shield',p,f,alloy)
    bottom=np.asarray(p)-[0,.002,0]
    shield_top_points=np.asarray(p).copy();shield_bottom_points=bottom.copy()
    model.mesh('rear.heat_shield.lower_sheet',bottom,[tuple(reversed(q)) for q in f],alloy)
    edges={}
    for face in f:
        for i in range(3):
            edge=tuple(sorted((face[i],face[(i+1)%3])));edges[edge]=edges.get(edge,0)+1
    for i,((a,b),count) in enumerate(edges.items()):
        if count==1:plate(f'rear.heat_shield.real_sheet_edge.{i}',[p[a],p[b],bottom[b],bottom[a]],alloy)
    for side in [-1,1]:
        for z in [-2.34,-2.06]:
            y=float(np.interp(z,zs,shield_ys))
            cylinder(f'rear.heat_shield.side_rail_mount.{side}.{z}',(side*.54,.722,z),(side*.80,.72,z),.008,frame,8)
            cylinder(f'rear.heat_shield.airgap_standoff.{side}.{z}',(side*.54,y,z),(side*.54,.722,z),.008,frame,8)
            cylinder(f'rear.heat_shield.retaining_bolt.{side}.{z}',(side*.54,y-.003,z),(side*.54,y+.003,z),.006,alloy,6)

    # A bolted engine bash plate ends ahead of the silencer and tailpipes.
    plan=[(-.42,.465,-.91),(.42,.465,-.91),(.55,.38,-1.20),(.55,.38,-1.88),(.47,.43,-2.03),(-.47,.43,-2.03),(-.55,.38,-1.88),(-.55,.38,-1.20)]
    sheet=[]
    for z,y,w in [(-.91,.465,.42),(-1.20,.38,.55),(-1.88,.38,.55),(-2.03,.43,.47)]:
        sheet.append([(-w,y,z),(0,y,z),(w,y,z)])
    model.grid('rear.bash_plate.serviceable_engine_guard_top',sheet,alloy,flip=True)
    model.grid('rear.bash_plate.real_six_mm_sheet_bottom',np.asarray(sheet)-[0,.006,0],alloy)
    # Visible folded perimeter gives the 6 mm sheet a physical edge.
    for i,a in enumerate(plan):
        b=plan[(i+1)%len(plan)];plate(f'rear.bash_plate.folded_edge.{i}',[a,b,(b[0],b[1]-.006,b[2]),(a[0],a[1]-.006,a[2])],alloy)
    for side in [-1,1]:
        for z in [-1.18,-1.83]:
            box(f'rear.bash_plate.frame_mount_tab.{side}.{z}',(side*.565,.394,z),(.10,.020,.12),frame,.004,2)
            cylinder(f'rear.bash_plate.removable_bolt.{side}.{z}',(side*.535,.369,z),(side*.535,.391,z),.012,alloy,6)

    # Bumper loads have their own brackets into the cradle. It wraps behind
    # the muffler; the rolled exhaust mouths sit 70 mm inside its rear face.
    path=[(-.90,.78,-2.10),(-.96,.78,-2.34),(-.89,.78,-2.52),(-.76,.78,-2.59),(.76,.78,-2.59),(.89,.78,-2.52),(.96,.78,-2.34),(.90,.78,-2.10)]
    polyline('rear.bumper.independent_wrap_guard',fillet_open(path),.035,frame,12)
    for side in [-1,1]:
        polyline(f'rear.bumper.chassis_load_strut.{side}.False',
            [(side*.80,.38,-2.05),(side*.915,.40,-2.27),(side*.948,.78,-2.34)],.033,frame,12)
        cylinder(f'rear.bumper.chassis_load_strut.{side}.True',
            (side*.80,.72,-2.28),(side*.948,.78,-2.34),.028,frame,12)
        box(f'rear.bumper.frame_mount_plate.{side}',(side*.80,.40,-2.05),(.12,.14,.025),frame,.008,3)
        for dx in [-.038,.038]:cylinder(f'rear.bumper.mount_bolt.{side}.{dx}',(side*.80+dx,.40,-2.03),(side*.80+dx,.40,-2.07),.012,alloy,6)

    tips=np.concatenate([part['p'] for part in model.parts[first:] if part['name'].startswith('rear.exhaust.twin_open_tailpipe.')])
    bumper=next(part['p'] for part in model.parts[first:] if part['name']=='rear.bumper.independent_wrap_guard')
    tip_rear_z=float(tips[:,2].min());guard_rear_z=float(bumper[:,2].min())
    case_points=np.concatenate([part['p'] for part in model.parts[first:]
        if part['name'].startswith(('rear.exhaust.transverse_oval_silencer_case.',
                                   'rear.exhaust.silencer_axial_neck_and_endcap.'))])
    case_top_y=float(case_points[:,1].max())
    shield_bottom_y=float(shield_bottom_points[:,1].min())
    shield_top_y=float(shield_top_points[:,1].max())
    rear_shield_top_y=float(shield_top_points[shield_top_points[:,2]<=-2.115,1].max())
    return dict(parts=len(model.parts)-first,triangles=sum(len(p['f']) for p in model.parts[first:]),
                hinge_crossmember=dict(x_end=.72,y=.36,z=-.30),
                frame_rails=dict(lowerX=.60,lowerY=.38,aftOuterLowerX=.80,
                    aftUpperX=.80,aftUpperY=.72,upperCradleFrontZ=-1.62,
                    upperPaths=[path for path in cold_paths if path['name'].startswith('rear.frame.upper_side_rail.')],
                    rearCrossmember=[[-.80,.72,-2.44],[.80,.72,-2.44]]),
                muffler=dict(center=[0,.53,-2.19],length=1.12,verticalRadius=.110,foreAftRadius=.155,
                    topology='two bank end-neck inlets; two separately opened rear-case outlets'),
                enginePackaging=dict(frontMostZ=-1.58,lowerCrankcaseRearZ=-1.97,
                    upperCrankcaseRearZ=-2.11,sumpCenter=[0,.55,-1.7675],
                    sumpRadii=[.275,.110,.1875],mountStations=[-1.66,-1.86],
                    limits='fictional cast relief and compact sump; not a production engine specification'),
                tip=dict(centers=[[-.13,.49,-2.555],[.13,.49,-2.555]],outerRadius=.052,innerRadius=.0485,hasDiskCaps=False),
                guard_rear_face_z=guard_rear_z,actual_tip_rear_z=tip_rear_z,tip_setback_inside_guard=tip_rear_z-guard_rear_z,
                muffler_top_y=case_top_y,heatshield_lower_y=shield_bottom_y,
                muffler_heatshield_airgap=shield_bottom_y-case_top_y,
                body_keepout_reference_y=.755,heatshield_max_y=shield_top_y,
                shield_keepout_plane_gap_at_rear=.755-rear_shield_top_y,
                shield_keepout_plane_min_gap=.755-shield_top_y,
                airgapMetric='actual case/shield vertical extents; Y.755 is a nominal packaging plane, not a measured body-triangle clearance',
                bashplate_end_z=-2.03,
                clearanceAudit=dict(version=1,hotPaths=hot_paths,coldPaths=cold_paths,
                    collectors=collector_surfaces,requiredHotStructureGap=.020,
                    enginePortInterfaces=[dict(header=f'rear.exhaust.bank_header.{side}.{j}',
                        cylinderBank=f'rear.engine.cylinder_bank.{side}',
                        center=[side*.455,.67,z],rootEndX=side*.505,
                        scope='named initial 50mm engine-port joint only; actual surface intersection still prohibited')
                        for side in [-1,1] for j,z in enumerate([-1.63,-1.80,-1.97])],
                    source='same authored mesh paths; conservative tube envelopes, not separate fitted proxies',
                    intendedInterfaces=['header start at its named engine port/flange',
                        'header end at its separate collector inlet',
                        'collector exit to bank inlet', 'bank inlet to axial case neck',
                        'case openings to their outlet necks', 'outlet neck to tailpipe',
                        'exhaust clamp/hanger contact; rubber remains off the hot case']),
                limits='Original visually plausible rear-engine packaging; not certified mechanical fitment.')
