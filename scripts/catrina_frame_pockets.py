"""Connected fabricated frame pockets around the actual spring-seat sweep.

Original game geometry based on boxed-steel kick-up and reinforced suspension
pocket construction, not a manufacturer frame or a structural certification.
The rig hardpoints and wheel motion are unchanged. Called after ram towers.
"""
import numpy as np


ORIGINAL_RAIL=np.array([[.57,.27,2.39],[.57,.27,1.53],
    [.22,.25,.40],[.12,.25,-.20],[.52,.29,-1.46],[.58,.32,-2.30]])


def original_station(z):
    return np.array([np.interp(z,ORIGINAL_RAIL[::-1,2],ORIGINAL_RAIL[::-1,0]),
                     np.interp(z,ORIGINAL_RAIL[::-1,2],ORIGINAL_RAIL[::-1,1]),z])


def frame_members():
    """Positive-X member centerlines, section width and vertical depth."""
    z=1.5113;front_a=original_station(z+.280)+[-.015,0,0];front_b=original_station(z-.280)+[-.015,0,0]
    rear_a=original_station(-z-.280)+[-.012,0,0];rear_b=original_station(-z-.375)+[-.012,0,0]
    fa=front_a+[-.075,0,0];fb=front_b+[-.075,0,0];ra=rear_a+[-.075,0,0]
    paths=[
        ('original_front',[ORIGINAL_RAIL[0],front_a],.095,.130),
        ('front_entry',[front_a,fa],.055,.100),
        ('front_pocket',[fa,[.370,.660,z+.250],
            [.370,.660,z-.250],fb],.065,.100),
        ('front_entry',[fb,front_b],.055,.100),
        ('engine_cradle',[[.250,.345,1.725],[.320,.345,1.725],
            [.320,.650,1.725]],.055,.045),
        # Keep a continuous propeller-shaft corridor through the X waist.
        # The old120mm half-width narrowed into the live slip-shaft sweep.
        ('original_center',[front_b,ORIGINAL_RAIL[2],[.220,.250,-.200],
            original_station(-.45)],.095,.130),
        ('rear_outrigger',[[original_station(-.45)[0],.215,-.45],[.795,.215,-.45]],.050,.060),
        ('rear_underfloor',[[.795,.215,-.45],[.795,.215,-.95]],.050,.060),
        ('rear_riser',[[.795,.215,-.95],[.795,.770,-1.28]],.050,.060),
        ('rear_riser',[[.795,.770,-1.28],[.795,.770,-1.32]],.050,.060),
        ('rear_header',[[.795,.770,-1.32],[.270,.770,-1.32]],.060,.110),
        ('rear_pocket',[[.270,.770,-1.32],[.270,.770,-z-.280]],.095,.110),
        ('rear_header',[[.270,.770,-z-.280],[.490,.770,-z-.280]],.060,.110),
        ('rear_post_bridge',[[.490,.770,-z-.280],[.490,.770,-z-.375]],.060,.110),
        ('original_tail',[rear_a,rear_b,ORIGINAL_RAIL[-1]],.095,.130),
    ]
    return [(name,np.asarray(a,float),np.asarray(b,float),width,height)
            for name,path,width,height in paths for a,b in zip(path[:-1],path[1:])]


def member_basis(a,b):
    axis=(b-a)/np.linalg.norm(b-a)
    across=np.cross(axis,[0,1,0])if abs(axis[1])<.999 else np.array([1.,0,0])
    across/=np.linalg.norm(across)
    return np.c_[across,axis,np.cross(across,axis)]


def add_frame_pockets(ctx,coat):
    M,g,parent=ctx['M'],ctx['g'],ctx['parent'];body=ctx['body']
    # The side-engine mount advances35mm along the same cast bank, outside
    # the upper-arm rear/fore channel sweep, and lands on the raised rail.
    # Suspension/actuator hardpoints are untouched.
    if 'frame_pocket_scope'not in ctx:
        for p in M.parts:
            if p['name']in('engine.mount_boss','engine.mount_isolator'):p['p'][:,2]+=.035
    # Remove the superseded rails and their local top gussets. Keeping those
    # plates after rerouting would leave solid metal across the spring opening.
    def replaced(part):
        if part['name']=='chassis.boxed_X_rail' or part['name'].startswith('chassis.spring_pocket_'):return True
        if part['name']=='engine.mount_bracket':return True
        if part['name']=='hardware.boxed_bracket'and part['parent']==body:
            z=float((part['p']+M.origins[part['parent']])[:,2].mean())
            if abs(z-1.5113)<.35:return True
        if part['name'] in ('chassis.junction_gusset','chassis.gusset_plug_weld'):
            z=float((part['p']+M.origins[part['parent']])[:,2].mean())
            return min(abs(z-1.5113),abs(z+1.5113))<.20
        return False
    M.parts[:]=[p for p in M.parts if not replaced(p)]
    with parent(body):
        for side in (-1,1):
            for name,a,b,width,height in frame_members():
                a=a*np.array([side,1,1]);b=b*np.array([side,1,1]);B=member_basis(a,b)
                # Closed, softly edged steel box sections overlap10mm at each
                # welded junction. These are load paths, not masked-out rails.
                g.box('chassis.boxed_X_rail',(a+b)/2,(width,np.linalg.norm(b-a)+.010,height),coat,.007,B=B)
            # Fore/aft tower shoes stay on the original rail stations. Broad
            # web doublers reinforce the steep front pocket entrances.
            for z in (1.5113+.280,1.5113-.280):
                p=original_station(z)*[side,1,1]
                g.box('chassis.spring_pocket_web_doubler',p+[-side*.049,0,0],(.006,.115,.120),coat,.004)
            for upper in(False,True):
                for sign in(-1,1):
                    a=np.array([side*.18,.43 if upper else .25,1.5113+sign*((.16 if upper else .22)+.055)])
                    b=original_station(1.5113+sign*.28)*[side,1,1];b[0]-=side*.042
                    # Narrow axial tabs land on the invariant shaft ends,
                    # clear of the adjacent rotating bush sleeve/channel.
                    g.box('chassis.spring_pocket_arm_bracket',(a+b)/2,(.026,np.linalg.norm(b-a)+.010,.042),coat,.005,B=member_basis(a,b))
    ctx['frame_pocket_scope']={
        'construction':'Connected fabricated boxed steel kick-ups and spring pockets; retained ram-foot stations and engine-mount cradle',
        'frontCenter':[.370,.660,1.5113], 'frontSection':[.065,.100],
        'rearCenter':[.270,.770,-1.5113], 'rearSection':[.095,.110],
        'unchanged':['wheel centers','suspension pivots','hydraulic pivots','ram-tower feet','outer coachwork'],
        'limitation':'Original game-model fabrication interpretation; no structural strength or roadworthiness certification'}
