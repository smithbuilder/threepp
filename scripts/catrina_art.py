"""Shaped coachwork and fine original ornament for the La Catrina revision.

Installed into the generator before its construction calls. Geometry is original. Roof, hood, deck paint and the side-scroll mask derive from the supplied atlas
through the documented catrina_reference_paint.py pipeline.
"""
import math
import numpy as np
from PIL import Image, ImageDraw


def install(E):
    M=E['M'];g=E['g'];body=E['body'];parent=E['parent']
    paint,rose,chrome,silver,black,rubber,white,plum,piping,gold,steel,glass,lamp,tail,amber=[E[k] for k in ('paint','rose','chrome','silver','black','rubber','white','plum','pipe','gold','steel','glass','lamp','tail','amber')]
    TAU=math.tau;HUB=E['HUB'];ZAXLE=E['ZAXLE'];cylinder=E['cylinder'];torus=E['torus'];poly=E['poly']
    BODY_OFFSET=-.19
    CAB_OFFSET=-.23
    INTERIOR_OFFSET=-.15

    def box(name,c,size,mat,bevel=.015,B=None):
        """A true radius with dense edge rings, rather than a chamfered cube."""
        c=np.array(c);half=np.array(size)/2;rad=min(bevel,float(min(half))*.94);B=np.eye(3) if B is None else B
        p=[];n=[];f=[]
        for axis in range(3):
            for sign in (-1,1):
                o=[a for a in range(3) if a!=axis]
                vals=[]
                for a in o:
                    vals.append(sorted(set([-half[a],-half[a]+rad*.13,-half[a]+rad*.5,-half[a]+rad,half[a]-rad,half[a]-rad*.5,half[a]-rad*.13,half[a]])))
                start=len(p);count=len(vals[1])
                for a in vals[0]:
                    for b in vals[1]:
                        q=np.zeros(3);q[axis]=sign*half[axis];q[o[0]]=a;q[o[1]]=b
                        core=np.clip(q,-half+rad,half-rad);d=q-core;nn=d/max(np.linalg.norm(d),1e-12)
                        p.append(c+B@(core+nn*rad));n.append(B@nn)
                for a in range(len(vals[0])-1):
                    for b in range(count-1):
                        k=start+a*count+b;f.extend([(k,k+1,k+count),(k+1,k+count+1,k+count)])
        M.mesh(name,p,f,mat,normals=n)

    def tube(name,points,r,mat,n=10):
        """Smooth swept trim with continuous normals through every bend."""
        q=np.asarray(points,float)
        if len(q)<2:return
        q=q[np.r_[True,np.linalg.norm(np.diff(q,axis=0),axis=1)>1e-8]]
        if len(q)<2:return
        tangent=np.gradient(q,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        p=[];norm=[];f=[];last=None
        for i,t in enumerate(tangent):
            ref=np.array([0,1,0]) if abs(t[1])<.85 else np.array([0,0,1])
            a=np.cross(t,ref);a/=np.linalg.norm(a)
            if last is not None and np.dot(a,last)<0:a=-a
            b=np.cross(t,a);last=a
            for j in range(n+1):
                d=a*math.cos(TAU*j/n)+b*math.sin(TAU*j/n);p.append(q[i]+r*d);norm.append(d)
        for i in range(len(q)-1):
            for j in range(n):
                a=i*(n+1)+j;f.extend([(a,a+1,a+n+1),(a+1,a+n+2,a+n+1)])
        M.mesh(name,p,f,mat,normals=norm)

    E['box']=box;E['tube']=tube
    # Candy pigment is dielectric beneath its clear lacquer; the metallic base
    # is represented subtly, leaving the chrome a distinct optical material.
    for material in (paint,rose):
        M.materials[material]['pbrMetallicRoughness'].update(baseColorFactor=g.linear(0xb72563)+[1],metallicFactor=.25,roughnessFactor=.20)
        M.materials[material]['extensions']['KHR_materials_clearcoat']={'clearcoatFactor':.80,'clearcoatRoughnessFactor':.06}
    M.materials[plum]['pbrMetallicRoughness'].update(roughnessFactor=.56,metallicFactor=0)
    M.materials[E['red']]['pbrMetallicRoughness'].update(roughnessFactor=.35,metallicFactor=0)
    M.materials[steel]['pbrMetallicRoughness'].update(roughnessFactor=.46,metallicFactor=0)
    M.materials[chrome]['pbrMetallicRoughness'].update(roughnessFactor=.08,metallicFactor=.97)
    M.materials[glass]['pbrMetallicRoughness'].update(baseColorFactor=[.38,.46,.46,.12],metallicFactor=0,roughnessFactor=.07)
    M.materials[lamp].pop('emissiveFactor',None)
    M.materials[lamp]['pbrMetallicRoughness'].update(baseColorFactor=[.56,.57,.53,1],metallicFactor=.42,roughnessFactor=.19)
    lensglass=M.mat('sealed_beam_lens',0xd9e0de,.10,0,alpha=.24)
    opticglass=M.mat('molded_optical_glass',0xe1e4df,.15,0,alpha=.50)
    reflector=M.mat('vacuum_aluminized_reflector',0xeeefeb,.12,1)
    rearalloy=M.mat('bright_formed_aluminum',0xededeb,.24,1)
    M.materials[tail]['pbrMetallicRoughness'].update(metallicFactor=.03,roughnessFactor=.19)
    M.materials[tail]['emissiveFactor']=[.045,.0006,.0015]
    M.materials[tail]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':.7,'clearcoatRoughnessFactor':.13}}

    def scroll(d,cx,cy,scale,color,width=1):
        for side in (-1,1):
            curve=[]
            for t in np.linspace(0,math.pi*2.9,55):
                r=scale*(.04+.068*t);curve.append((cx+side*(r*math.cos(t)+scale*.16),cy+r*math.sin(t)*.75))
            d.line(curve,fill=color,width=width)
            # Finely branching leaves belong to the spiral rather than dots.
            for angle in np.linspace(1.5,7,8):
                r=scale*(.04+.068*angle);px=cx+side*(r*math.cos(angle)+scale*.16);py=cy+r*math.sin(angle)*.75
                leaf=[(px,py)]
                for t in np.linspace(0,1,12):leaf.append((px+side*scale*.17*math.sin(t*math.pi)*math.cos(angle)-side*scale*.08*t*math.sin(angle),py+scale*.16*t*math.cos(angle)+scale*.07*math.sin(t*math.pi)*math.sin(angle)))
                d.line(leaf,fill=color,width=width)

    def textures():
        # Author at double resolution then filter to the enforced 1K budget.
        rng=np.random.default_rng(1964);N=2048
        from catrina_reference_paint import create_paint
        reference,receipt=create_paint()
        E['reference_paint_provenance']=receipt
        height=.94*(1-np.arange(512)/511)
        blend=np.clip((.632-height)/.030,0,1);blend=blend*blend*(3-2*blend)
        # Explicit Candy / Shell pink swatches in the supplied finish palette.
        pigment=np.array([183,37,99])*(1-blend[:,None])+np.array([247,143,180])*blend[:,None]
        arr=np.broadcast_to(pigment[:,None,:],(512,N,3)).copy().astype(np.float32)
        noise=rng.normal(0,.9,(512,N,1));arr+=noise
        flake=rng.random((512,N))>.996;arr[flake]+=[9,7,7]
        side=Image.fromarray(np.uint8(np.clip(arr,0,255)))
        # A separate narrow UV field keeps the original scroll at useful texel
        # density. It follows the actual stamped side, including the arch cuts.
        ornament=Image.new('RGBA',(N,256),(0,0,0,0))
        band=(.72-.630)/.18*256;strip_h=round(.042/.18*256)
        strip=reference['side_scroll'].resize((369,strip_h),Image.Resampling.LANCZOS).convert('RGBA')
        for k,x in enumerate(range(0,N,369)):
            tile=strip if k%2==0 else strip.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            ornament.paste(tile,(x,round(band-strip_h/2)))
        d=ImageDraw.Draw(ornament)
        for h in (.605,.609,.651,.655):
            yy=(.72-h)/.18*256;d.line((0,yy,N,yy),fill='#cba26c',width=2)
        def cameo(profile):
            im=Image.new('RGBA',(512,512),(0,0,0,0));c=ImageDraw.Draw(im)
            dark='#721c3d';light='#d9b37b';goldcol='#cba26c'
            c.ellipse((8,8,504,504),fill=goldcol)
            c.ellipse((22,22,490,490),fill=dark)
            c.ellipse((35,35,477,477),outline='#e3c18c',width=5)
            if profile:
                # Original La Catrina profile: feathered hat, skull profile,
                # neck and lace collar, with a clear dark eye and jaw break.
                c.polygon([(236,322),(287,323),(300,368),(365,427),(256,466),(164,426),(224,371)],fill=light)
                c.polygon([(210,172),(283,164),(325,198),(328,255),(348,278),(323,287),(322,315),(297,344),(241,339),(220,304),(203,278),(195,232)],fill=light)
                c.ellipse((224,218,265,247),fill=dark)
                c.polygon([(296,247),(319,263),(295,272)],fill=dark)
                c.line([(282,303),(319,299)],fill=dark,width=8)
                for x in (289,300,311):c.line((x,296,x+2,317),fill=dark,width=4)
                c.polygon([(173,180),(187,126),(265,107),(310,130),(316,179)],fill=goldcol)
                c.ellipse((112,159,366,205),fill=light)
                c.arc((178,69,329,181),195,330,fill=light,width=15)
                c.line([(252,123),(291,73),(315,57)],fill=light,width=9)
                for yy,xx in ((75,303),(89,292),(102,280)):
                    c.line([(xx-16,yy-8),(xx,yy),(xx+18,yy-3)],fill=light,width=6)
                for x,y in ((213,407),(241,425),(273,425),(302,404)):
                    c.ellipse((x-9,y-9,x+9,y+9),outline=dark,width=4)
            else:
                # A separate frontal calavera; no hat, visible cheekbones,
                # broad eye sockets and a squared row of teeth.
                c.ellipse((125,100,387,349),fill=light)
                c.polygon([(166,282),(346,282),(332,395),(297,427),(215,427),(180,395)],fill=light)
                c.ellipse((158,202,234,278),fill=dark);c.ellipse((278,202,354,278),fill=dark)
                c.polygon([(254,271),(237,316),(273,316)],fill=dark)
                c.line((193,357,319,357),fill=dark,width=9)
                for x in (211,234,257,280,303):c.line((x,342,x,391),fill=dark,width=6)
                c.arc((211,124,302,196),180,360,fill=dark,width=7)
                for x in (173,339):c.ellipse((x-14,167,x+14,195),fill=dark)
            return im
        for z,width,height,profile in ((-.48,.150,.120,True),(-2.03,.075,.075,False)):
            w=round(width/5.33*N);h=round(height/.18*256)
            icon=cameo(profile).resize((w,h),Image.Resampling.LANCZOS)
            x=round((2.665+BODY_OFFSET-z)/5.33*N-w/2)
            ornament.alpha_composite(icon,(x,round(band-h/2)))
        sm=E['image_mat']('candy_scroll_side',side.resize((1024,256),Image.Resampling.LANCZOS),.10,.28)
        decal=E['image_mat']('champagne_side_ornament',ornament.resize((1024,128),Image.Resampling.LANCZOS),.25,.20)
        M.materials[decal].update(alphaMode='MASK',alphaCutoff=.22)
        roof=E['image_mat']('reference_roof_lace',reference['roof'],.10,.29)
        hood=E['image_mat']('reference_hood_lace',reference['hood'],.10,.29)
        deck=E['image_mat']('reference_deck_lace',reference['deck'],.10,.29)
        for mat in (sm,decal,roof,hood,deck):
            M.materials[mat]['pbrMetallicRoughness'].update(metallicFactor=.25,roughnessFactor=.20)
            M.materials[mat]['extensions']['KHR_materials_clearcoat']={'clearcoatFactor':.80,'clearcoatRoughnessFactor':.06}
        E['side_ornament_material']=decal
        receipt['authoredCameos']={'door':{'width':.150,'height':.120,'type':'Original vector La Catrina profile with feathered hat'},'rear':{'width':.075,'height':.075,'type':'Original vector frontal calavera'},'basis':'Side elevation outer cameo approximately30x24 pixels and rear15x15 pixels;578px wheelbase=3.0226m. Conservative150x120mm and75mm authored sizes.','texture':'Separate1024x128 masked narrow field, physicalY.54.. .72m; source scroll and original vector cameos.'}
        return sm,roof,hood,deck

    # The initial low-detail texture calls have already populated two slots.
    # Replace the image/material slots in place so unrelated names stay stable.
    oldside,oldtop=E['sidepaint'],E['toppaint'];M.images.clear()
    sidepaint,toppaint,hoodpaint,deckpaint=textures()
    E['sidepaint']=sidepaint;E['toppaint']=toppaint

    from scipy.interpolate import PchipInterpolator
    side_profile=PchipInterpolator(
        [.16,.20,.29,.34,.40,.49,.57,.605,.630,.654,.68,.73,.79,.84,.875,.90,.925],
        [.925,.945,.970,.980,.979,.994,1.001,1.010,1.010,1.004,.995,.989,.985,.977,.961,.932,.88])
    def smoothstep(a,b,x):
        t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
    def side_x(y,z=0):
        # Real stamped transverse sections: tucked rocker, shallow lower swage,
        # proud spear shoulder, then an eased fender crown.
        end_drop=.025*smoothstep(2.35,2.55,abs(z-BODY_OFFSET))
        section_y=y+end_drop*smoothstep(.70,.82,y)
        shape=float(side_profile(min(.925,max(.16,section_y))))
        taper=.025*max(0,(abs(z-BODY_OFFSET)-2.24)/.36)**2
        # A small longitudinal fender swell avoids an extruded rectangular shell.
        swell=.006*math.exp(-((abs(z)-1.55)/.65)**2)
        # The central pressed field continues across the door cut to both
        # arches. Its ends taper inward near the rocker, as on the reference.
        inset=.035*(1-smoothstep(.245,.435,y))
        recess=0
        for a,b in ((-1.19,1.18),(-2.66,-1.90),(1.91,2.28)):
            qz=abs(z-(a+b)*.5)-((b-a)*.5-.030-inset)
            qy=abs(y-.340)-.065
            distance=math.hypot(max(qz,0),max(qy,0))+min(max(qz,qy),0)-.030
            # A shallow crisp pressed channel with a rounded drawn end. The
            # end taper eases continuously, without a pinched diagonal crease
            # or a broad blurred transition across the whole lower panel.
            recess=max(recess,1-smoothstep(-.023,.004,distance))
        return shape-taper+swell-.0075*recess

    def arch_bottom(z):
        # Front arch follows the tyre; the rear skirt is a low, softly flattened
        # opening, as shown in the supplied side elevations.
        f=z-ZAXLE;r=z+ZAXLE
        front=HUB+math.sqrt(max(0,.315**2-f*f)) if abs(f)<=.315+1e-9 else .18
        rear=HUB+.170*math.sqrt(max(0,1-(r/.335)**4)) if abs(r)<=.335+1e-9 else .18
        toe=.18
        for center,radius in ((ZAXLE,.315),(-ZAXLE,.335)):
            distance=abs(z-center)-radius
            if 0<distance<.035:toe=max(toe,.215-math.sqrt(max(0,.035**2-(.035-distance)**2)))
        # The body terminates ABOVE the bumper's wrapped upper roll. The old
        # low return projected through it as a conspicuous pink knife point.
        return max(.18+.325*smoothstep(2.34,2.55,abs(z-BODY_OFFSET)),front,rear,toe)

    def side_upper(z):return .90-.050*smoothstep(2.35,2.55,abs(z-BODY_OFFSET))
    def deck_half_width(z):return .825-.040*max(0,(abs(z-BODY_OFFSET)-2.25)/.30)**2
    def hood_rear_z(x):return .79+.21*max(0,1-(x/.916)**2)
    def trunk_front_z(x):return -1.55-.065*max(0,1-(x/.916)**2)

    def deck_height(x,z,front):
        # The bonnet has two softly crowned panels separated by a narrow spine.
        # A long eased nose/deck roll joins the fascia without a vertical lip.
        nose=smoothstep(2.35,2.55,abs(z-BODY_OFFSET))
        crown=.018*(1-(x/.825)**2)
        paired=(.006*math.sin(min(1,abs(x)/.825)*math.pi)**2+.008*math.exp(-(x/.035)**2)) if front else 0
        cowl=.017*max(0,1-(x/.825)**2)*(1-smoothstep(hood_rear_z(x),hood_rear_z(x)+.16,z)) if front else 0
        normal=.916+crown+paired-cowl
        end=(.830+.025*smoothstep(.49,.58,abs(x))) if front else (.832+.018*smoothstep(.49,.58,abs(x)))
        return normal*(1-nose)+end*nose

    def shoulder_height(x,z,front):
        """Common crown boundary used by shoulder skin and end header."""
        x=abs(x);x0=deck_half_width(z)+.004
        upper=side_upper(z);x1=side_x(upper,z)
        if x<=x0:return deck_height(x,z,front)-.002*smoothstep(x0-.004,x0,x)
        dx=x1-x0
        start=deck_height(x0,z,front)-.002
        m0=(deck_height(x0+.0001,z,front)-deck_height(x0-.0001,z,front))/.0002
        m1=.0002/(side_x(upper+.0001,z)-side_x(upper-.0001,z))
        # Concentrate the outer radius in a 35mm rolled edge. One wide cubic
        # made the fender crown bulge above the intended nose/tail section.
        join=x1-min(.035,dx*.45);peak=max(start,upper)+.002
        if x<join:
            length=join-x0;t=(x-x0)/length;a,b,ma,mb=start,peak,m0,0
        else:
            length=x1-join;t=(x-join)/length;a,b,ma,mb=peak,upper,0,m1
        return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*length*ma+(-2*t**3+3*t*t)*b+(t**3-t*t)*length*mb

    E['deck_height']=deck_height;E['deck_half_width']=deck_half_width

    E['side_x']=side_x;E['arch_bottom']=arch_bottom
    oldshell=E['shell']
    def shell():
        oldshell()
        # Replace only exterior side/deck sheet geometry. Keep every validated
        # floor, bulkhead, opening hinge and wheel clearance surface.
        M.parts[:]=[p for p in M.parts if not (p['name'].startswith(('body.quarter','body.door','body.fender','body.arch_return','body.deck_shoulder','body.hood','body.trunk','trim.hood_edge','trim.trunk_edge','trim.arch_lip')) and p['name'] not in ('body.trunk_center_floor','body.trunk_aft_floor'))]
        M.parts[:]=[p for p in M.parts if p['name'] not in ('trim.side_spear','trim.belt_rail','body.wheel_well_liner')]
        for p in M.parts:
            if p['name']=='body.firewall':p['p'][:,2]+=INTERIOR_OFFSET
            # The structural floor is underbody-coated steel. Its exposed
            # front edge can be seen through the front wheel opening; the
            # cabin's separate carpet already covers the interior upper face.
            if p['name']=='body.cabin_floor':p['mat']=black
        for nm in ('hood_hinge','trunk_hinge'):
            node=next(i for i,n in enumerate(M.nodes) if n['name']==nm)
            M.origins[node][2]+=CAB_OFFSET;M.nodes[node]['translation'][2]+=CAB_OFFSET
        for s in (-1,1):
            for za,zb,name in ((-2.55+BODY_OFFSET,-.57,'quarter'),(-.566,.71,'door'),(.714,2.55+BODY_OFFSET,'fender')):
                rows=[];uv=[]
                # Door fields are nearly invariant along their length; keep
                # the full transverse stamping section without redundant rows.
                zs=list(np.linspace(za,zb,max(32,int((zb-za)*(24 if name=='door' else 100)))))
                for center,radius in ((ZAXLE,.315),(-ZAXLE,.335)):
                    zs.extend(z for z in (center-radius-.001,center-radius,center+radius,center+radius+.001) if za<z<zb)
                    for sign in (-1,1):
                        zs.extend(z for z in center+sign*(radius+np.linspace(0,.035,8)) if za<z<zb)
                for z in sorted(set(zs)):
                    lo=arch_bottom(z)
                    # Preserve fixed stamping bands through each arch. Stretching
                    # every horizontal row to the lip twists lower swage faces.
                    upper=side_upper(z)
                    ys=np.clip(np.linspace(.18,.90,75),lo,upper)
                    rows.append([(s*side_x(y,z),y,z) for y in ys]);uv.append([((2.665+BODY_OFFSET-z)/5.33,1-y/.94) for y in ys])
                M.grid('body.'+name,rows,sidepaint,uv,flip=s>0)
                # Evaluate the actual stamped-surface derivative rather than
                # averaging faces along clipped arch/top rows. The latter
                # creates false diagonal reflection creases at end shoulders.
                pp=M.parts[-1];norm=[];eps=.0001
                for x,y,z in pp['p']+M.origins[pp['parent']]:
                    dy=(side_x(y+eps,z)-side_x(y-eps,z))/(2*eps)
                    dz=(side_x(y,z+eps)-side_x(y,z-eps))/(2*eps)
                    n=np.array([s,-dy,-dz]);norm.append(n/np.linalg.norm(n))
                pp['n']=np.asarray(norm,np.float32)
            for z0,rr in ((ZAXLE,.315),(-ZAXLE,.335)):
                contour=[(z0-rr-.035+.035*math.cos(a),.215-.035*math.sin(a)) for a in np.linspace(math.pi/2,0,10)]
                contour +=[(z0-rr,HUB)]
                contour += [(z,arch_bottom(z)) for z in np.linspace(z0-rr,z0+rr,95)[1:-1]]
                contour += [(z0+rr,HUB)]
                contour +=[(z0+rr+.035-.035*math.cos(a),.215-.035*math.sin(a)) for a in np.linspace(0,math.pi/2,10)]
                rows=[];line=[];back=[]
                for z,y in contour:
                    x=side_x(y,z)
                    # Rolled 27mm flange preserves the opening and clears the
                    # actual steered/bumped tire sweep with the audit allowance.
                    rows.append([(s*x,y,z),(s*(x-.012),y+.004,z),(s*(x-.027),y+.008,z)])
                    back.append([(s*x,y+.003,z),(s*(x-.012),y+.007,z),(s*(x-.027),y+.011,z)])
                    line.append((s*(x+.002),y+.004,z))
                def side_uv(grid):return [[((2.665+BODY_OFFSET-z)/5.33,1-y/.94) for x,y,z in row] for row in grid]
                M.grid('body.arch_return',rows,sidepaint,side_uv(rows),flip=s<0);tube('trim.arch_lip',line,.0047,chrome,10)
                M.grid('body.arch_return_inner',back,sidepaint,side_uv(back),flip=s>0)
                hem=[[a[-1],b[-1]] for a,b in zip(rows,back)]
                M.grid('body.arch_folded_hem',hem,sidepaint,side_uv(hem),flip=s<0)
                for j in (0,-1):
                    cap=[[a,b] for a,b in zip(rows[j],back[j])]
                    M.grid('body.arch_end_cap',cap,sidepaint,side_uv(cap),flip=(s<0)==(j==0))
                # Outward flare meets the housing already validated around
                # the native tire sweep. The superseded semicircular liner
                # left a visible crown gap and crossed the steered tire.
                flare=[];upright=[];crown_return=[]
                zs=sorted(set([*np.linspace(z0-.415,z0+.415,75),z0-rr-.001,z0-rr,z0+rr,z0+rr+.001]))
                for z in zs:
                    low=arch_bottom(z);crown=max(.600,.42+.400*math.sqrt(max(0,1-((z-z0)/.415)**2)))
                    flare.append([(s*(side_x(low,z)-.027),low+.011,z),(s*(side_x(low+.025,z)-.009),low+.025,z)])
                    # Follow the actual concave shoulder rather than spanning
                    # it with one straight triangle. The old chord breached
                    # the candy skin by 2.47mm above both front arches.
                    # Keep the transverse stamping stations rather than many
                    # uniformly spaced samples; clipping retains the exact
                    # moving lower and upper boundaries at every z station.
                    ys=np.clip([.205,.245,.290,.340,.400,.490,.570,.605,.630,.654,.680,.730,.790,.820],low+.025,crown)
                    upright.append([(s*(side_x(y,z)-.009),y,z) for y in ys])
                    crown_return.append([(s*(side_x(crown,z)-.009),crown,z),(s*.930,crown,z)])
                for surface in (flare,upright,crown_return):
                    M.grid('body.wheel_well_liner',surface,black,flip=s<0)
                    if surface is upright:
                        # Narrow triangles at the vertical arch toes skew
                        # averaged normals. This wall lies on side_x minus a
                        # constant inset, so its actual inward derivative is
                        # known exactly and does not need a face average.
                        pp=M.parts[-1];norm=[];eps=.0001
                        for x,y,z in pp['p']+M.origins[pp['parent']]:
                            dy=(side_x(y+eps,z)-side_x(y-eps,z))/(2*eps)
                            dz=(side_x(y,z+eps)-side_x(y,z-eps))/(2*eps)
                            n=np.array([-s,dy,dz]);norm.append(n/np.linalg.norm(n))
                        pp['n']=np.asarray(norm,np.float32)
                # Fore/aft splash panels complete the tub at its existing safe
                # end stations. The lower central opening remains available
                # to the arms/axle; no sheet crosses those moving components.
                for end in ((-1,1) if z0>0 else ()):
                    z=z0+end*.415;top=.600
                    # A drawn splash apron rolls away from the tyre rather
                    # than presenting a flat closing plate. The upper inboard
                    # return screens the engine while leaving the lower arm
                    # and frame opening unobstructed. All shared boundaries
                    # use the same absolute-height curve.
                    notch=.650 if end>0 else .510
                    bottom_inner=.395 if end<0 else .375
                    def apron_point(x,y):
                        outer=side_x(y,z)-.009
                        u=(x-.380)/(outer-.380)
                        dz=.045*math.sin(math.pi*u)*math.sin(math.pi*(y-.185)/(.600-.185))
                        return (s*x,y,z+end*dz)
                    for inner in (True,False):
                        curtain=[];bottom=bottom_inner if inner else .185
                        for t in np.linspace(0,1,8):
                            y=bottom+(top-bottom)*t;outer=side_x(y,z)-.009
                            xs=np.linspace(.380,notch,5) if inner else np.linspace(notch,outer,7)
                            curtain.append([apron_point(x,y) for x in xs])
                        M.grid('body.wheel_well_end_curtain',curtain,black,flip=(s<0)==(end<0))
                        back=np.asarray(curtain)+[0,0,end*.003]
                        M.grid('body.wheel_well_end_curtain',back,black,flip=(s<0)!=(end<0))
                        edge=[*curtain[0],*[r[-1] for r in curtain[1:]],*curtain[-1][-2::-1],*[r[0] for r in curtain[-2:0:-1]],curtain[0][0]]
                        for a,b in zip(edge[:-1],edge[1:]):
                            M.grid('body.wheel_well_apron_edge',[[a,np.array(a)+[0,0,end*.003]],[b,np.array(b)+[0,0,end*.003]]],black)
                    rim=[apron_point(x,bottom_inner) for x in np.linspace(.380,notch,9)]
                    rim +=[apron_point(notch,y) for y in np.linspace(bottom_inner,.185,9)[1:]]
                    tube('body.wheel_well_rail_notch',rim,.003,black,8)
            # A shaped masked paint layer, 0.35mm above the continuous panel.
            # UVs devote their full height to the gold spear and cameos.
            rows=[];uv=[]
            for z in np.linspace(-2.52+BODY_OFFSET,2.52+BODY_OFFSET,221):
                ys=np.clip(np.linspace(.54,.72,19),arch_bottom(z)+.001,.72)
                rows.append([(s*(side_x(y,z)+.00035),y,z) for y in ys])
                uv.append([((2.665+BODY_OFFSET-z)/5.33,(.72-y)/.18) for y in ys])
            M.grid('body.side_ornament',rows,E['side_ornament_material'],uv,flip=s>0)
            pp=M.parts[-1];norm=[];eps=.0001
            for x,y,z in pp['p']+M.origins[pp['parent']]:
                dy=(side_x(y+eps,z)-side_x(y-eps,z))/(2*eps)
                dz=(side_x(y,z+eps)-side_x(y,z-eps))/(2*eps)
                n=np.array([s,-dy,-dz]);norm.append(n/np.linalg.norm(n))
            pp['n']=np.asarray(norm,np.float32)
            # Door cutline follows the rounded lower corner and rising belt.
            for z in (-.57,.71):
                line=[(s*(side_x(y,z)+.0012),y,z) for y in np.linspace(.25,.887,45)]
                tube('body.door_gap',line,.0015,black,6)
            line=[(s*(side_x(.235,z)+.0015),.235,z) for z in np.linspace(-.545,.695,55)]
            tube('body.door_sill_gap',line,.0015,black,6)
            for y,rad in ((.651,.008),(.608,.007),(.245,.006)):
                line=[]
                zs=list(np.linspace(-2.52+BODY_OFFSET,2.52+BODY_OFFSET,145))
                cameo_gaps=[]
                for cz,rz,ry in ((-.48,.075,.060),(-2.03,.0375,.0375)):
                    dy=max(0,abs(y-.630)-rad)
                    if dy<ry:
                        half=rz*math.sqrt(1-(dy/ry)**2)+.001
                        cameo_gaps.append((cz-half,cz+half))
                        zs.extend((cz-half-.0005,cz-half,cz+half,cz+half+.0005))
                for center,radius in ((ZAXLE,.315),(-ZAXLE,.335)):
                    zs.extend([center-radius-.001,center+radius+.001])
                for z in sorted(zs):
                    # In the original sheet the oval interrupts the molding;
                    # continuous chrome here would obscure the painted face.
                    covered=any(a<=z<=b for a,b in cameo_gaps)
                    if y-rad>=arch_bottom(z) and not covered:line.append((s*(side_x(y,z)+.004),y,z))
                    else:
                        if len(line)>1:tube('trim.side_spear',line,rad,chrome,8)
                        line=[]
                if len(line)>1:tube('trim.side_spear',line,rad,chrome,8)
            tube('trim.belt_rail',[(s*.954,.902,z) for z in np.linspace(-1.28+CAB_OFFSET,1.08+CAB_OFFSET,45)],.007,chrome,8)
        for front,z0,z1 in ((True,.95+CAB_OFFSET,2.55+BODY_OFFSET),(False,-2.55+BODY_OFFSET,-1.28+CAB_OFFSET)):
            nm='hood' if front else 'trunk';node=next(i for i,n in enumerate(M.nodes) if n['name']==nm+'_hinge')
            def decky(x,z):
                return deck_height(x,z,front)
            with parent(node):
                rows=[];uv=[]
                for v,z in zip(np.linspace(0,1,58),np.linspace(z0,z1,58)):
                    hw=deck_half_width(z)
                    row=[]
                    for x in np.linspace(-hw,hw,43):
                        zz=hood_rear_z(x)+(z1-hood_rear_z(x))*v if front else z0+(trunk_front_z(x)-z0)*v
                        row.append((x,decky(x,zz),zz))
                    rows.append(row);uv.append([(u,v) for u in np.linspace(0,1,43)])
                M.grid('body.'+nm,rows,hoodpaint if front else deckpaint,uv)
                inner=np.array(rows).copy()
                for iz in range(inner.shape[0]):
                    vz=iz/(inner.shape[0]-1)
                    for ix in range(inner.shape[1]):
                        ux=ix/(inner.shape[1]-1)
                        # Four pressed relief wells leave a perimeter flange,
                        # central spine and cross-web in one continuous skin.
                        well=(math.sin(ux*math.pi*2)**4)*(math.sin(vz*math.pi*2)**4)
                        inner[iz,ix,1]-=.025-.010*well
                M.grid('body.'+nm+'_inner',inner,rose,uv,flip=True)
                # Sheet metal folded edge gives the opened panel real thickness.
                for side in (-1,1):
                    line=[];ret=[]
                    for z in np.linspace(hood_rear_z(side*.825) if front else z0,z1 if front else trunk_front_z(side*.825),58):
                        x=side*deck_half_width(z);y=decky(x,z)
                        line.append((x,y-.001,z));ret.append([(x,y,z),(x,y-.025,z)])
                    M.grid('body.'+nm+'_hem',ret,paint,flip=side<0);tube('body.'+nm+'_gap',line,.0018,black,6)
                for endz in (z0,z1):
                    hw=deck_half_width(endz)
                    end=[]
                    for x in np.linspace(-hw,hw,43):
                        zz=hood_rear_z(x) if front and endz==z0 else trunk_front_z(x) if not front and endz==z1 else endz
                        end.append([(x,decky(x,zz),zz),(x,decky(x,zz)-.025,zz)])
                    M.grid('body.'+nm+'_end_hem',end,paint,flip=endz==max(z0,z1))
                    if front and endz==z0:tube('body.hood_cowl_gap',[r[0] for r in end],.0018,black,6)
                    if not front and endz==z1:tube('body.trunk_cowl_gap',[r[0] for r in end],.0018,black,6)
                hinge_z=z0 if front else z1
                direction=1 if front else -1
                for sx in (-.52,.52):
                    attach_z=(hood_rear_z(sx)+.045) if front else (trunk_front_z(sx)-.045)
                    leaf_y=decky(sx,attach_z)-.035
                    box('body.'+nm+'_hinge_leaf',(sx,leaf_y,(hinge_z+attach_z)*.5),(.055,.020,abs(attach_z-hinge_z)+.025),steel,.006)
                    cylinder('body.'+nm+'_hinge_pin',(sx-.044,.901,hinge_z),(sx+.044,.901,hinge_z),.009,chrome,14)
                    for zz in (attach_z-direction*.025,attach_z):
                        cylinder('body.'+nm+'_hinge_bolt',(sx,leaf_y-.012,zz),(sx,leaf_y+.015,zz),.005,silver,6)
            for sx in (-.52,.52):
                box('body.'+nm+'_hinge_anchor',(sx,.870,hinge_z),(.073,.043,.055),steel,.006)
            for s in (-1,1):
                rows=[]
                for z in np.linspace(min(z0,z1),max(z0,z1),61):
                    x0=deck_half_width(z)+.004
                    upper=side_upper(z);x1=side_x(upper,z)
                    row=[]
                    for t in np.linspace(0,1,16):
                        x=x0+(x1-x0)*t
                        y=shoulder_height(x,z,front)
                        row.append((s*x,y,z))
                    rows.append(row)
                M.grid('body.deck_shoulder',rows,paint,flip=s<0)
                pp=M.parts[-1];norm=[];eps=.0001
                for x,y,z in pp['p']+M.origins[pp['parent']]:
                    dx=(shoulder_height(x+eps,z,front)-shoulder_height(x-eps,z,front))/(2*eps)
                    dz=(shoulder_height(x,z+eps,front)-shoulder_height(x,z-eps,front))/(2*eps)
                    n=np.array([-dx,1,-dz]);norm.append(n/np.linalg.norm(n))
                pp['n']=np.asarray(norm,np.float32)

    E['shell']=shell

    def rounded_rect(cx,cy,hw,hh,r,n=12):
        q=[]
        for x,y,a in ((cx+hw-r,cy+hh-r,0),(cx-hw+r,cy+hh-r,math.pi/2),(cx-hw+r,cy-hh+r,math.pi),(cx+hw-r,cy-hh+r,math.pi*1.5)):
            q.extend([(x+r*math.cos(t),y+r*math.sin(t)) for t in np.linspace(a,a+math.pi/2,n,endpoint=False)])
        return q

    def ring_xy(name,cx,cy,z,hw,hh,r,width,depth,mat,back=False):
        outer=rounded_rect(cx,cy,hw,hh,r);inner=rounded_rect(cx,cy,hw-width,hh-width,max(.008,r-width));rows=[]
        for (x,y),(ix,iy) in zip(outer+[outer[0]],inner+[inner[0]]):
            rows.append([(x,y,z-depth),(x,y,z),(ix,iy,z+.003),(ix,iy,z-depth)])
        M.grid(name,rows,mat,flip=back)

    def fascia_top(x,front):
        center,outer=(.755,.805) if front else (.762,.800)
        return center+(outer-center)*smoothstep(.49,.58,abs(x))

    def fascia_outline(front):
        edge=fascia_top(.91,front);bottom=.492 if front else .505;r=.040
        pts=[(x,fascia_top(x,front)) for x in np.linspace(-.91,.91,91)]
        pts += [(.91+r*math.cos(a),edge-r+r*math.sin(a)) for a in np.linspace(math.pi/2,0,15)[1:]]
        pts += [(.95,y) for y in np.linspace(edge-r,bottom+r,20)[1:]]
        pts += [(.91+r*math.cos(a),bottom+r+r*math.sin(a)) for a in np.linspace(0,-math.pi/2,15)[1:]]
        pts += [(x,bottom) for x in np.linspace(.91,-.91,70)[1:]]
        pts += [(-.91+r*math.cos(a),bottom+r+r*math.sin(a)) for a in np.linspace(-math.pi/2,-math.pi,15)[1:]]
        pts += [(-.95,y) for y in np.linspace(bottom+r,edge-r,20)[1:]]
        pts += [(-.91+r*math.cos(a),edge-r+r*math.sin(a)) for a in np.linspace(math.pi,math.pi/2,15)[1:-1]]
        return pts

    def fascia_ring(name,front,z,material,width=.014):
        points=fascia_outline(front);rows=[];sgn=1 if front else -1
        for i,p in enumerate(points):
            tangent=np.asarray(points[(i+1)%len(points)])-np.asarray(points[i-1]);tangent/=np.linalg.norm(tangent)
            inner=np.asarray(p)+width*np.array([tangent[1],-tangent[0]])
            rows.append([(p[0],p[1],z-sgn*.025),(p[0],p[1],z),(inner[0],inner[1],z+sgn*.002),(inner[0],inner[1],z-sgn*.025)])
        rows.append(rows[0]);M.grid(name,rows,material,flip=front)

    def fascia_fill(name,front,z,material):
        edge=fascia_top(.91,front);bottom=.492 if front else .505;r=.040;rows=[]
        for x in sorted(set([*np.linspace(-.95,.95,153),-.91,.91])):
            if abs(x)>.91:
                arc=math.sqrt(max(0,r*r-(abs(x)-.91)**2));lo=bottom+r-arc;hi=edge-r+arc
            else:lo=bottom;hi=fascia_top(x,front)
            rows.append([(x,lo,z),(x,hi,z)])
        M.grid(name,rows,material,flip=not front)

    def front_rear():
        first_part=len(M.parts);first_node=len(M.nodes)
        # End faces roll continuously into side fenders instead of box plates.
        for front in (True,False):
            sign=1 if front else -1;nm='front' if front else 'rear'
            rows=[]
            endz=sign*2.55+BODY_OFFSET;endwidth=side_x(side_upper(endz),endz)
            hw=deck_half_width(endz)
            xs=sorted(set([*np.linspace(-hw,hw,43),*np.linspace(hw+.004,endwidth,16),*np.linspace(-endwidth,-hw-.004,16)]))
            for x in xs:
                bow=.021*(1-(x/.94)**2)
                forrow=[]
                for t in np.linspace(0,1,14):
                    top=shoulder_height(x,sign*2.55+BODY_OFFSET,front)
                    bottom=fascia_top(x,front)+.002
                    y=bottom+(top-bottom)*t
                    z=sign*(2.551+bow*(1-t))
                    forrow.append((x,y,z))
                rows.append(forrow)
            M.grid(nm+'.painted_header',rows,paint,flip=not front)
            # Painted eyebrow and radiused front/rear outer cheek.
            outline=fascia_outline(front)
            for s in (-1,1):
                rows=[]
                for t in np.linspace(0,1,22):
                    angle=t*math.pi/2;z=sign*(2.55-.12*(1-math.cos(angle)))
                    rows.append([(s*(.94+(side_x(y,z+BODY_OFFSET)-.94)*math.sin(angle)),y,z) for y in np.linspace(.505,side_upper(z+BODY_OFFSET),26)])
                M.grid(nm+'.fender_roll',rows,paint,flip=(s>0)!=front)
                # Close the narrow return from the actual side stamping into
                # the end fascia, including the lower rocker and upper corner.
                rows=[]
                for y in np.linspace(arch_bottom(endz),side_upper(endz),45):
                    outer=side_x(y,sign*2.55+BODY_OFFSET);inner=min(.920,outer-.007)
                    rows.append([(s*(outer+(inner-outer)*t),y,sign*(2.55+.015*math.sin(t*math.pi/2))) for t in np.linspace(0,1,12)])
                M.grid(nm+'.closed_side_return',rows,paint,flip=(s<0)==front)
            tube('trim.'+nm+'_eyebrow',[(x,y,sign*2.583) for x,y in outline+[outline[0]]],.004,chrome,10)
            box(nm+'.lower_valance',(0,.38,sign*2.51),(1.84,.28,.07),sidepaint,.045)
        # Fine horizontal grille ribs continue behind the inset lamp bezels.
        fascia_fill('front.grille_recess',True,2.563,black)
        fascia_ring('front.formed_grille_surround',True,2.600,chrome,.012)
        box('front.inner_fascia',(0,.645,2.532),(1.865,.365,.035),rose,.040)
        for y in np.linspace(.514,.786,12):
            line=[]
            for x in np.linspace(-.925,.925,111):
                if y<fascia_top(x,True)-.013:line.append((x,y,2.579+.006*(1-(x/.93)**2)))
                else:
                    if len(line)>1:tube('front.horizontal_grille',line,.0027,chrome,6)
                    line=[]
            if len(line)>1:tube('front.horizontal_grille',line,.0027,chrome,6)
        for x in np.linspace(-.91,.91,21):
            tube('front.vertical_grille',[(x,.514,2.576),(x,fascia_top(x,True)-.014,2.576)],.0014,silver,6)
        for s in (-1,1):
            ring_xy('front.headlamp_pod',s*.735,.66,2.619,.214,.120,.052,.012,.044,chrome)
            for x in (s*.635,s*.824):
                cylinder('front.headlamp_dark',(x,.670,2.566),(x,.670,2.580),.091,black,64)
                # Recessed paraboloid, concentric formed bezel and convex lens.
                rows=[]
                for a in np.linspace(0,TAU,65):
                    rows.append([(x+r*math.cos(a),.670+r*math.sin(a),2.585+.042*(r/.083)**2) for r in np.linspace(.004,.083,12)])
                M.grid('front.headlamp_reflector',rows,reflector,flip=True)
                torus('front.headlamp_outer_bezel',(x,.670,2.626),.091,.0052,chrome,axis=(0,0,1),segments=64,sides=10)
                torus('front.headlamp_inner_bezel',(x,.670,2.632),.084,.0025,silver,axis=(0,0,1),segments=64,sides=7)
                rows=[]
                for a in np.linspace(0,TAU,65):rows.append([(x+r*math.cos(a),.670+r*math.sin(a),2.638+.014*(1-(r/.082)**2)) for r in np.linspace(.001,.082,14)])
                M.grid('front.sealed_beam_cover',rows,lensglass,flip=True)
                for dx in np.linspace(-.067,.067,17):
                    h=math.sqrt(max(0,.081**2-dx**2));line=[]
                    for yy in np.linspace(-h,h,7):line.append((x+dx,.670+yy,2.639+.014*(1-(dx*dx+yy*yy)/.081**2)))
                    tube('front.lens_flute',line,.00065,opticglass,5)
                for yy in np.linspace(-.052,.052,7):
                    h=math.sqrt(.081**2-yy*yy);tube('front.lens_horizontal',[(x-h,.670+yy,2.640),(x+h,.670+yy,2.640)],.00045,opticglass,5)
                for a in (math.pi/2,math.pi*1.5):cylinder('front.bezel_screw',(x+.088*math.cos(a),.670+.088*math.sin(a),2.63),(x+.088*math.cos(a),.670+.088*math.sin(a),2.634),.0025,steel,8)
        # A wide pressed bumper has crown, apron, returns and the characteristic
        # shallow V at center; it is not a collection of thin circular bars.
        def bumper_curve(parameter):
            if abs(parameter)<=.82:return parameter,2.612
            t=smoothstep(.82,.995,abs(parameter));angle=t*math.pi/2
            return math.copysign(.82+.165*math.sin(angle),parameter),2.612-.205*(1-math.cos(angle))
        def bumper_press(x,y):
            # A shallow pressed crown produces a changing reflection normal.
            # It returns to zero at the lips/ends and stays inside the envelope.
            face=smoothstep(-.126,-.080,y)*(1-smoothstep(.045,.066,y))
            ends=1-smoothstep(.79,.86,abs(x))
            vertical=max(0,1-((y+.015)/.065)**2)
            cheek=math.exp(-((abs(x)-.69)/.115)**4)
            return face*ends*(.010*(.65*vertical+.35*cheek)-.003)
        for front in (True,False):
            sign=1 if front else -1
            rows=[]
            bumper_profile=PchipInterpolator([-.150,-.126,-.066,.035,.066,.071],[-.024,.018,.045,.043,.020,-.011])
            for parameter in np.linspace(-.995,.995,153):
                x,zc=bumper_curve(parameter);yc=.383+.015*(abs(x)/.995)**1.4
                pocket=0 if front else .026*math.exp(-(x/.265)**8)
                center=math.exp(-(x/.28)**8);section=[]
                for y in np.linspace(-.150,.071,37):
                    yy=y-.014*center*(1-smoothstep(-.10,.02,y))+(.030 if front else .035)*smoothstep(.010,.071,y)
                    z=float(bumper_profile(y))+bumper_press(x,y)-pocket*(smoothstep(-.145,-.11,y)*(1-smoothstep(.045,.07,y)))
                    section.append((x,yc+yy,sign*(zc+z)))
                rows.append(section)
            M.grid('trim.bumper_beam',rows,chrome,flip=not front)
            # Rolled and closed end cheeks, not an open knife-edge profile.
            for sx,profile in ((-1,rows[0]),(1,rows[-1])):
                center=np.mean(np.asarray(profile),axis=0);cap=[]
                for p in profile:
                    q=center+(np.asarray(p)-center)*.91;q[0]=sx*.987;cap.append(q)
                M.grid('trim.bumper_end_roll',[[p,q] for p,q in zip(profile,cap)],chrome,flip=(sx<0)==front)
                verts=[*cap];faces=[(0,j,j+1) for j in range(1,len(verts)-1)]
                M.mesh('trim.bumper_end_cap',verts,faces,chrome,normals=[[sx,0,0]]*len(verts))
            for y in (-.132,.063):
                line=[]
                for parameter in np.linspace(-.995,.995,145):
                    x,zc=bumper_curve(parameter);center=math.exp(-(x/.28)**8)
                    yy=y-.014*center*(1-smoothstep(-.10,.02,y))+(.030 if front else .035)*smoothstep(.010,.071,y)
                    line.append((x,.383+.015*(abs(x)/.995)**1.4+yy,sign*(zc+float(bumper_profile(y))+bumper_press(x,y))))
                tube('trim.bumper_rolled_edge',line,.005,chrome,8)
            for s in (-1,1):
                box('trim.bumper_guard',(s*.54,.335,sign*2.641),(.038,.235,.047),chrome,.017,B=g.rotZ(s*.04))
                box('trim.bumper_mount',(s*.54,.35,sign*2.45),(.07,.07,.17),steel,.012)
            node=M.node('front_plate' if front else 'rear_plate',body,[0,.37,sign*2.62])
            if not front:
                with parent(node):
                    box('trim.plate_backing',(0,.335,sign*2.637),(.335,.150,.014),chrome,.009)
                    box('trim.plate',(0,.335,sign*2.646),(.308,.126,.005),rearalloy,.005)
                    ring_xy('trim.license_pocket',0,.335,sign*2.646,.187,.089,.022,.008,sign*.015,chrome,back=True)
                    for xx in (-.137,.137):
                        for yy in (.285,.385):cylinder('trim.plate_screw',(xx,yy,-2.650),(xx,yy,-2.654),.003,chrome,8)
            if front:
                for yy in (.285,.315,.345):
                    ribs=[]
                    for x in np.linspace(-.46,.46,61):ribs.append([(x,yy+d,2.658+.003*math.cos(d/.006*math.pi/2)) for d in np.linspace(-.006,.006,7)])
                    M.grid('trim.front_bumper_channel',ribs,chrome)
                for s in (-1,1):
                    box('front.signal_housing',(s*.775,.410,2.66),(.220,.067,.016),chrome,.016)
                    box('front.amber_lens',(s*.775,.411,2.669),(.187,.041,.005),amber,.008)
                    for x in np.linspace(s*.775-.082,s*.775+.082,17):tube('front.signal_lens_prism',[(x,.394,2.673),(x,.428,2.673)],.0006,gold,5)
        box('rear.tail_panel',(0,.650,-2.537),(1.86,.35,.032),paint,.06)
        fascia_ring('rear.inset_trim',False,-2.604,chrome,.015)
        # One continuously corrugated formed panel, including the spaces
        # between lamp pods. The former three isolated center rails left most
        # of the panel flat and visually dark against the densely ribbed atlas.
        rows=[];pitch=.017;amplitude=.0028
        xs=sorted(set([*np.linspace(-.91,.91,25),*np.linspace(.91,.95,7),*np.linspace(-.95,-.91,7),*np.linspace(.49,.58,8),*np.linspace(-.58,-.49,8)]))
        for x in xs:
            arc=math.sqrt(max(0,.040**2-max(0,abs(x)-.91)**2));lo=.545-arc;hi=fascia_top(x,False)-.040+arc
            rows.append([(x,y,-2.596-amplitude*math.cos(TAU*(y-.505)/pitch)) for y in np.clip(np.linspace(.505,.800,145),lo,hi)])
        M.grid('rear.dark_inset',rows,rearalloy,flip=True)
        pp=M.parts[-1];norm=[]
        for x,y,z in pp['p']+M.origins[pp['parent']]:
            derivative=amplitude*TAU/pitch*math.sin(TAU*(y-.505)/pitch)
            n=np.array([0,derivative,-1]);norm.append(n/np.linalg.norm(n))
        pp['n']=np.asarray(norm,np.float32)
        for s in (-1,1):
            for ax in (.444,.632,.820):
                x=s*ax
                torus('rear.tail_bezel',(x,.662,-2.624),.077,.0075,chrome,axis=(0,0,1),segments=56,sides=10)
                cylinder('rear.tail_recess',(x,.662,-2.590),(x,.662,-2.603),.073,black,40)
                def lens_z(r):return -2.628+.014*math.sin(math.pi*max(0,min(1,(r-.033)/.034)))
                rows=[]
                for a in np.linspace(0,TAU,49):rows.append([(x+r*math.cos(a),.662+r*math.sin(a),lens_z(r)) for r in np.linspace(.033,.067,13)])
                M.grid('rear.tail_lens',rows,tail)
                for r in (.052,.061):torus('rear.tail_lens_ring',(x,.662,lens_z(r)-.0008),r,.0012,tail,axis=(0,0,1),segments=40,sides=5)
                torus('rear.inner_optical_bezel',(x,.662,-2.635),.035,.0028,chrome,axis=(0,0,1),segments=48,sides=7)
                rows=[]
                for a in np.linspace(0,TAU,49):rows.append([(x+r*math.cos(a),.662+r*math.sin(a),-2.638-.009*(1-(r/.029)**2)) for r in np.linspace(.001,.029,10)])
                M.grid('rear.central_optical_dome',rows,tail)
                for a in np.linspace(0,TAU,20,endpoint=False):tube('rear.lens_radial',[(x+r*math.cos(a),.662+r*math.sin(a),lens_z(r)-.0007) for r in np.linspace(.039,.064,4)],.0007,tail,5)
                for a in np.linspace(0,TAU,4,endpoint=False):
                    xx=x+.062*math.cos(a);yy=.662+.062*math.sin(a);zz=lens_z(.062)-.002
                    cylinder('rear.lens_retaining_screw',(xx,yy,zz+.002),(xx,yy,zz-.001),.0028,chrome,8)
        tube('rear.center_badge',[(-.063,.679,-2.624),(0,.642,-2.627),(.063,.679,-2.624)],.004,chrome,8)
        tube('front.hood_ornament',[(0,.936,2.38),(0,.958,2.42),(0,.947,2.49)],.0038,chrome,8)
        for part in M.parts[first_part:]:
            if part['parent']==body:part['p'][:,2]+=BODY_OFFSET
        for node in range(first_node,len(M.nodes)):
            M.origins[node][2]+=BODY_OFFSET;M.nodes[node]['translation'][2]+=BODY_OFFSET

    E['front_rear']=front_rear

    def roof_and_glass():
        first_part=len(M.parts)
        # A compound-curved hardtop with a crowned center, rolled gutters, and
        # rounded fore/aft corners; width contracts at the front and rear cap.
        def roofwidth(z):return .788-.026*(abs((z+.19)/.72)**6)
        def roofy(x,z):
            t=(z+.19)/.72
            # A genuine longitudinal crown carries the hardtop down into its
            # headers. The previous quartic18mm drop stayed nearly flat across
            # the middle and read as a thin visor in the side silhouette.
            return 1.300+.029*(1-(x/.80)**2)-.046*t*t
        def roofpoint(u,v):
            z=-.91+1.44*v;w=roofwidth(z)
            # The windscreen/header wraps forward at center in plan; the
            # backlight uses the corresponding smaller rearward bow.
            zz=z+(.10*v**4-.045*(1-v)**4)*(1-u*u)
            # Evaluate the crown at the actual bowed header station. Giving
            # the forward-bowed center the side station's height created a
            # conspicuous raised tip above the windshield.
            return np.array([u*w,roofy(u*w,zz),zz])
        def roofedge(z,s=1):return np.array([s*(roofwidth(z)+.010),roofy(roofwidth(z),z)-.017,z])
        def roof_fold(a,radius):
            turn=smoothstep(math.pi/2,math.pi,a)
            return radius*math.sin(a),-.017*(1-math.cos(a))-.012*turn
        def upper_ease(t):
            if t<=.72:return t
            u=(t-.72)/.28;q=.18
            # C1-continuous bend seats the post into the roof's rising tangent;
            # the old sine segment changed slope at its start and flattened
            # completely at the roof, leaving an angular connection.
            return .72+.28*((q-1)*u**3+(1-q)*u*u+u)
        rows=[];uv=[]
        for v in np.linspace(0,1,60):
            rows.append([roofpoint(u,v) for u in np.linspace(-1,1,55)]);uv.append([(u,v) for u in np.linspace(0,1,55)])
        M.grid('cab.lace_roof',rows,toppaint,uv)
        # The smooth upholstered underside needs fewer samples than the
        # reflective painted crown; keep the complete boundary in both axes.
        iz=sorted(set([*range(0,len(rows),2),len(rows)-1]));ix=sorted(set([*range(0,len(rows[0]),2),len(rows[0])-1]))
        lining=np.asarray(rows)[np.ix_(iz,ix)]-[0,.037,0]
        M.grid('cab.roof_headliner',lining,plum,flip=True)
        for s in (-1,1):
            rows=[];drip=[]
            for z in np.linspace(-.91,.53,60):
                w=roofwidth(z);y=roofy(w,z)
                rows.append([(s*(w+roof_fold(a,.010)[0]),y+roof_fold(a,.010)[1],z) for a in np.linspace(0,math.pi,17)])
                drip.append(roofedge(z,s))
            M.grid('cab.folded_roof_edge',rows,paint,flip=s<0);tube('trim.roof_drip',drip,.0065,chrome,10)
            M.grid('cab.roof_inner_return',[[row[-1],(s*roofwidth(row[-1][2]),roofy(roofwidth(row[-1][2]),row[-1][2])-.037,row[-1][2])] for row in rows],plum,flip=s>0)
        for z,front in ((-.91,False),(.53,True)):
            rows=[]
            for u in np.linspace(-1,1,55):
                p=roofpoint(u,1 if front else 0)
                rows.append([p+[0,roof_fold(a,.018)[1],(1 if front else -1)*roof_fold(a,.018)[0]] for a in np.linspace(0,math.pi,17)])
            M.grid('cab.roof_end_return',rows,paint,flip=front)
            M.grid('cab.roof_header_inner_return',[[row[-1],roofpoint(u,1 if front else 0)-[0,.037,0]] for u,row in zip(np.linspace(-1,1,55),rows)],plum,flip=not front)
            # Rounded corner patches join the side and end folded sections.
            # Previously their separate half-rolls met at an exposed pole.
            for s in (-1,1):
                center=roofpoint(s,1 if front else 0);verts=[];norm=[];faces=[];direction=1 if front else -1
                for j,phi in enumerate(np.linspace(0,math.pi/2,9)):
                    for k,a in enumerate(np.linspace(0,math.pi,17)):
                        dx,dy=roof_fold(a,.010);dz,_=roof_fold(a,.018)
                        verts.append(center+[s*dx*math.cos(phi),dy,direction*dz*math.sin(phi)])
                        t=max(0,min(1,(a-math.pi/2)/(math.pi/2)))
                        slope=.017*math.sin(a)+.012*6*t*(1-t)/(math.pi/2)
                        n=np.array([s*slope*math.cos(phi)/.010,math.cos(a),direction*slope*math.sin(phi)/.018]);norm.append(n/np.linalg.norm(n))
                        if j and k:
                            v=(j-1)*17+k-1;faces.extend([(v,v+17,v+1),(v+1,v+17,v+18)])
                M.mesh('cab.roof_corner_return',verts,faces,paint,normals=norm)
        for s in (-1,1):
            a=np.array([s*.933,.910,1.01]);b=roofedge(.53,s)
            line=[]
            for t in np.linspace(0,1,41):
                v=upper_ease(t);p=a+(b-a)*v;p[2]=a[2]+(b[2]-a[2])*t;line.append(p)
            # Both the painted post radius and its chrome lie beneath the
            # roof crown. The upper tangent turns continuously into the gutter.
            tube('cab.A_post',line,.0165,paint,12)
            cap=[];norm=[];faces=[]
            tangents=np.gradient(np.asarray(line),axis=0)
            for j,(p,tangent) in enumerate(zip(line,tangents)):
                tangent/=np.linalg.norm(tangent);q=np.array([s*.75,0,.65]);q-=tangent*np.dot(tangent,q);q/=np.linalg.norm(q);b=np.cross(tangent,q)
                for angle in np.linspace(-.9,.9,7):
                    n=q*math.cos(angle)+b*math.sin(angle);cap.append(p+.0172*n);norm.append(n)
                if j:
                    for k in range(6):a=(j-1)*7+k;faces.extend([(a,a+7,a+1),(a+1,a+7,a+8)])
            M.mesh('trim.A_post',cap,faces,chrome,normals=norm)
            inside=[p+[-s*.008,-.031*upper_ease(t),-.015*(1-upper_ease(t))] for p,t in zip(line,np.linspace(0,1,len(line)))]
            M.grid('trim.A_post_weatherseal',[[p+[-s*.001,-.004,0],q] for p,q in zip(line,inside)],black,flip=s>0)
            tube('trim.A_post_inner_edge',inside,.0024,chrome,7)
            rows=[];uv=[]
            for t in np.linspace(0,1,35):
                v=upper_ease(t);row=[]
                for u in np.linspace(0,1,19):
                    lower=np.array([s*.948,.904,-1.30+.31*u]);upper=roofedge(-.91+.27*u,s)
                    p=lower+(upper-lower)*v;p[2]=lower[2]+(upper[2]-lower[2])*t
                    p[0]+=s*.009*math.sin(u*math.pi)*math.sin(t*math.pi);row.append(p)
                rows.append(row)
                uv.append([(u*.30,t*.30) for u in np.linspace(0,1,19)])
            M.grid('cab.C_pillar',rows,toppaint,uv,flip=s<0)
            inner=np.asarray(rows).copy();inner[:,:,0]-=s*.022
            M.grid('cab.C_pillar_lining',inner,plum,flip=s>0)
            for j in (0,-1):
                M.grid('cab.C_pillar_return',[[a[j],b[j]] for a,b in zip(rows,inner)],paint,flip=(s>0)==(j==0))
            for j in (0,-1):
                M.grid('cab.C_pillar_return',[[a,b] for a,b in zip(rows[j],inner[j])],paint,flip=(s<0)==(j==0))
            for back in (True,False):
                pts=[row[0 if back else -1] for row in rows]
                tube('trim.rear_post',pts,.006,chrome,8)
                if not back:
                    inside=[p+[-s*.008,-.031*upper_ease(t),.014*(1-upper_ease(t))] for p,t in zip(pts,np.linspace(0,1,len(pts)))]
                    M.grid('trim.rear_post_weatherseal',[[p+[-s*.001,-.004,0],q] for p,q in zip(pts,inside)],black,flip=s<0)
                    tube('trim.rear_post_inner_edge',inside,.0024,chrome,7)
            rail=[roofedge(z,s) for z in np.linspace(-.64,.53,50)]
            chrome_rows=[[p+[s*dx,dy,0] for dx,dy in ((-.004,.006),(.003,.005),(.005,0),(.003,-.005),(-.002,-.007))] for p in rail]
            M.grid('trim.window_top',chrome_rows,chrome,flip=s<0)
            M.grid('trim.window_top_weatherseal',[[p+[-s*.001,-.006,0],p+[-s*.008,-.031,0]] for p in rail],black,flip=s<0)
            tube('trim.window_top_inner_edge',[p+[-s*.008,-.031,0] for p in rail],.0024,chrome,7)
        for front in (True,False):
            lowz,highz=(1.01,.53) if front else (-1.30,-.91);rows=[]
            for t in np.linspace(0,1,35):
                v=upper_ease(t);row=[]
                w=.916+(.756-.916)*v
                for u in np.linspace(-1,1,45):
                    top=roofpoint(u,1 if front else 0);top[0]=u*.756;top[1]-=.039
                    low=np.array([u*.916,.919+.008*(1-u*u),lowz+(.20 if front else -.065)*(1-u*u)])
                    p=low+(top-low)*v
                    p[2]=low[2]+(top[2]-low[2])*t
                    row.append(p)
                rows.append(row)
            M.grid('cab.windshield' if front else 'cab.backlight',rows,glass,flip=front)
            border=[*rows[0],*[r[-1] for r in rows[1:]],*rows[-1][-2::-1],*[r[0] for r in rows[-2:0:-1]]]
            # A continuous pressed surround, with softened joins instead of
            # four independent straight poles crossing at sharp corners.
            border=np.asarray(border)
            for _ in range(2):border=np.asarray([q for a,b in zip(border,np.roll(border,-1,axis=0)) for q in (.75*a+.25*b,.25*a+.75*b)])[::2]
            tube('trim.glass_rubber',[*border,border[0]],.007,black,8)
            tube('trim.glass_surround',[p+[0,.001,.002 if front else -.002] for p in [*border,border[0]]],.0045,chrome,8)
        for s in (-1,1):
            cylinder('trim.mirror_stalk',(s*.957,.90,.73),(s*1.035,.99,.684),.007,chrome,12)
            center=np.array([s*1.035,1.012,.678]);rows=[]
            for a in np.linspace(0,TAU,49):
                rows.append([center+[r*math.cos(a),r*math.sin(a),.012*(1-(r/.052)**2)] for r in np.linspace(.001,.052,9)])
            M.grid('trim.mirror_back',rows,chrome,flip=True)
            cylinder('trim.mirror_rim',center+[0,0,-.008],center+[0,0,0],.052,chrome,48)
            cylinder('trim.mirror_glass',center+[0,0,-.009],center+[0,0,-.010],.046,silver,48)
            torus('trim.mirror_rolled_edge',center+[0,0,-.008],.049,.003,chrome,axis=(0,0,1),segments=48,sides=7)
        def windscreen_point(x,t):
            v=upper_ease(t);w=.916+(.756-.916)*v;u=x/w
            top=roofpoint(u,1);top[0]=u*.756;top[1]-=.039
            low=np.array([u*.916,.919+.008*(1-u*u),1.01+.20*(1-u*u)])
            p=low+(top-low)*v;p[2]=low[2]+(top[2]-low[2])*t
            return p+[0,.004,.003]
        for x in (-.35,.32):
            tube('trim.wiper_arm',[windscreen_point(x,.015),windscreen_point(x+.025,.16)],.003,steel,7)
            tube('trim.wiper',[windscreen_point(x-.12,.125),windscreen_point(x+.14,.195)],.0035,steel,8)
        cowl=[]
        for x in np.linspace(-.916,.916,81):
            gz=1.01+.20*(1-(x/.916)**2);hz=hood_rear_z(x)-CAB_OFFSET
            gy=.919+.008*(1-(x/.916)**2)-.004;hy=shoulder_height(x,hz+CAB_OFFSET,True)-.002
            cowl.append([(x,gy+(hy-gy)*t,gz+(hz-gz)*t) for t in np.linspace(0,1,5)])
        M.grid('cab.cowl',cowl,paint,flip=True)
        rear_cowl=[]
        for x in np.linspace(-.916,.916,81):
            gz=-1.30-.065*(1-(x/.916)**2);hz=trunk_front_z(x)-CAB_OFFSET
            gy=.919+.008*(1-(x/.916)**2)-.004;hy=shoulder_height(x,hz+CAB_OFFSET,False)-.002
            rear_cowl.append([(x,gy+(hy-gy)*t,gz+(hz-gz)*t) for t in np.linspace(0,1,5)])
        M.grid('cab.rear_cowl',rear_cowl,paint)
        for x in np.linspace(-.68,.68,55):
            gz=1.01+.20*(1-(x/.916)**2);hz=hood_rear_z(x)-CAB_OFFSET
            y=.919+.008*(1-(x/.916)**2)-.003
            poly('cab.cowl_vent',[(x-.0015,y,gz+.004),(x-.0015,y,hz-.004),(x+.0015,y,hz-.004),(x+.0015,y,gz+.004)],black)
        for part in M.parts[first_part:]:part['p'][:,2]+=CAB_OFFSET
        # Both side windows are lowered in the reference's pillarless hardtop.
        M.parts[:]=[p for p in M.parts if p['name'] not in ('cab.quarter_glass','trim.quarter_divider')]

    E['roof_and_glass']=roof_and_glass
    oldinterior=E['interior']
    def interior():
        first_part=len(M.parts)
        oldinterior()
        M.parts[:]=[p for p in M.parts if not p['name'].startswith(('interior.bench_','interior.seat_pleat','interior.back_pleat','interior.steering_column','interior.steering_spoke','interior.steering_hub')) and p['name']!='interior.dashboard']
        # A thin rolled dashboard section, rather than a broad padded box.
        from scipy.interpolate import CubicSpline
        section=np.array([[.735,.660],[.778,.649],[.818,.655],[.844,.681],[.850,.726],[.844,.785],[.832,.890],[.775,.899],[.735,.660]])
        curve=CubicSpline(np.arange(len(section)),section,bc_type='periodic')
        rows=[]
        for x in np.linspace(-.835,.835,31):
            rows.append([(x,yy+.006*(1-(x/.835)**2),zz+.008*(x/.835)**4) for yy,zz in curve(np.linspace(0,len(section)-1,49))])
        M.grid('interior.dashboard',rows,plum,flip=True)
        for side,row in ((-1,rows[0]),(1,rows[-1])):
            M.mesh('interior.dashboard_end',row,[(0,j,j+1) for j in range(1,len(row)-2)],plum,normals=[[side,0,0]]*len(row))
        cylinder('interior.steering_column',(-.53,.68,.68),(-.53,.784,.435),.017,steel,20)
        for a in (0,2.1,4.2):
            c=np.array([-.53,.795,.424]);tip=np.array([-.53+.162*math.cos(a),.795+.155*math.sin(a),.41-.047*math.sin(a)])
            # Thin flattened dished spokes and a small tapered horn center.
            direction=tip-c;across=np.cross(direction,[0,.30,1]);across/=np.linalg.norm(across)
            pts=[c-across*.007,c+across*.007,tip+across*.004,tip-across*.004]
            poly('interior.steering_spoke',pts,chrome);poly('interior.steering_spoke',[p+[0,.002,.001] for p in pts[::-1]],chrome)
        cylinder('interior.steering_hub',(-.53,.795,.443),(-.53,.795,.412),.028,chrome,28,r2=.021)
        cylinder('interior.horn_button',(-.53,.795,.412),(-.53,.795,.408),.018,plum,28)
        torus('interior.horn_ring',(-.53,.795,.424),.120,.0027,chrome,axis=(0,.30,1),segments=48,sides=6)
        # Close the inward-facing rocker and footwell structure between the
        # validated low floor and upholstered door card. The exterior stamping
        # is single-sided and cannot serve as an interior wall.
        for s in (-1,1):
            box('interior.carpeted_sill',(s*.866,.335,-.02),(.028,.175,1.79),plum,.012)
            box('interior.front_kick_panel',(s*.845,.470,.765),(.030,.430,.150),plum,.015)
            box('interior.rear_quarter_liner',(s*.858,.560,-.965),(.040,.565,.260),plum,.018)
        box('interior.floor_carpet',(0,.263,.105),(1.72,.008,2.04),plum,.003)
        for z,w in ((.24,1.48),(-.78,1.50)):
            # Understructure and softly upholstered, indented pleats are separate.
            box('interior.bench_base',(0,.40,z),(w,.16,.51),plum,.060)
            box('interior.bench_back',(0,.685,z-.228),(w,.49,.14),plum,.060,B=g.rotX(-.12))
            rows=[]
            for zz in np.linspace(z-.22,z+.23,24):
                # Fade pleat relief before its sewn perimeter. Constant waves
                # at the old cut edge produced a visible saw-tooth fringe.
                edge=(1-smoothstep(.17,.225,abs(zz-z)))
                rows.append([(x,.515+.020*(1-(x/(w/2))**8)+.007*edge*(1-smoothstep(w*.43,w*.48,abs(x)))*math.cos((x/w+.5)*math.pi*44)-.013*((zz-z)/.24)**4,zz) for x in np.linspace(-w*.48,w*.48,177)])
            M.grid('interior.pleated_cushion',rows,plum)
            # Pleated upholstery wraps around the actual rounded backrest
            # section and over its crest, rather than ending at a flat bar.
            profile=[(yy,.070,smoothstep(-.175,-.125,yy)) for yy in np.linspace(-.175,.185,23)]
            profile +=[(.185+.060*math.sin(a),.010+.060*math.cos(a),1) for a in np.linspace(0,math.pi/2,9)[1:]]
            profile +=[(.245,-.010,1)]
            profile +=[(.185+.060*math.cos(a),-.010-.060*math.sin(a),1-smoothstep(0,math.pi/2,a)) for a in np.linspace(0,math.pi/2,6)[1:]]
            rows=[];B=g.rotX(-.12);half=np.array([w/2,.245,.070]);center=np.array([0,.685,z-.228])
            for yy,zz,taper in profile:
                row=[]
                for x in np.linspace(-w*.48,w*.48,177):
                    q=np.array([x,yy,zz]);core=np.clip(q,-half+.060,half-.060);d=q-core;n=d/max(np.linalg.norm(d),1e-12)
                    skin=core+n*(.060+taper*(.004+.0032*math.cos((x/w+.5)*math.pi*44)))
                    row.append(center+B@skin)
                rows.append(row)
            M.grid('interior.pleated_back',rows,plum,flip=True)
            # Bolster seam outline and restrained contrast stitching.
            border=[(-w*.48,.524,z+.21),(w*.48,.524,z+.21),(w*.48,.524,z-.20),(-w*.48,.524,z-.20),(-w*.48,.524,z+.21)]
            tube('interior.bench_piping',border,.0024,piping,7)
            for x in np.linspace(-w*.45,w*.45,23):tube('interior.seat_stitch',[(x,.525,z+.17),(x,.532,z-.16)],.00065,piping,5)
            for s in (-1,1):
                box('interior.seatbelt_buckle',(s*.28,.546,z+.07),(.038,.015,.058),chrome,.008)
                box('interior.seatbelt_webbing',(s*.28,.537,z-.05),(.032,.006,.20),black,.002)
        # Door cards gain chromed crank/pull, quilt channels and lower carpet.
        for s in (-1,1):
            box('interior.lower_carpet',(s*.866,.410,-.02),(.011,.16,1.42),black,.006)
            for z in np.linspace(-.62,.61,19):tube('interior.door_pleat',[(s*.864,.50,z),(s*.864,.71,z)],.002,piping,6)
            tube('interior.window_crank',[(s*.846,.68,.39),(s*.831,.65,.45)],.006,chrome,8)
            cylinder('interior.crank_knob',(s*.822,.65,.45),(s*.843,.65,.45),.012,plum,12)
            for zz in (-.64,.64):cylinder('interior.door_fastener',(s*.856,.75,zz),(s*.865,.75,zz),.003,chrome,8)
        # Radio dial, pushbuttons, glovebox seam, pedals and rearview mirror.
        box('interior.radio',(0,.795,.645),(.30,.070,.016),chrome,.008)
        box('interior.radio_scale',(0,.807,.634),(.20,.023,.004),black,.003)
        for x in np.linspace(-.07,.07,5):box('interior.radio_button',(x,.776,.628),(.020,.010,.013),white,.003)
        for x in (-.135,.135):cylinder('interior.radio_knob',(x,.799,.634),(x,.799,.622),.012,chrome,14)
        tube('interior.glovebox_seam',[(.27,.826,.651),(.71,.826,.651),(.71,.747,.651),(.27,.747,.651)],.0012,black,5)
        cylinder('interior.glovebox_lock',(.49,.787,.649),(.49,.787,.640),.008,chrome,12)
        for x in (-.57,-.43):box('interior.pedal',(x,.32,.64),(.07,.09,.025),rubber,.010,B=g.rotX(-.2))
        cylinder('interior.rearview_stem',(0,1.259,.51),(0,1.19,.48),.005,chrome,10)
        box('interior.rearview_mirror',(0,1.181,.48),(.20,.054,.018),chrome,.014)
        box('interior.rearview_surface',(0,1.181,.469),(.18,.040,.003),silver,.009)
        for part in M.parts[first_part:]:
            if part['name'].startswith(('interior.door_','interior.window_crank','interior.crank_knob','interior.arm_rest','interior.lower_carpet')):
                part['p'][:,2]=.07+(part['p'][:,2]+.03)*.79
            else:part['p'][:,2]+=INTERIOR_OFFSET
        M.parts[:]=[p for p in M.parts if p['name']!='interior.rear_shelf']
        quarter_front=min(p['p'][:,2].min() for p in M.parts if p['name']=='interior.door_card')+.012
        # Closed quarter upholstery and parcel shelf are actual inward skins,
        # independent of the exterior's single-sided painted sheet.
        for s in (-1,1):
            rows=[]
            for z in np.linspace(-1.53,quarter_front,31):
                rows.append([(s*(side_x(y,z)-.045),y,z) for y in np.linspace(.72,.895,9)])
            M.grid('interior.upper_quarter_card',rows,plum,flip=s<0)
            rows=[[(s*(side_x(.895,z)-.045),.895,z),(s*side_x(.9,z),.9,z)] for z in np.linspace(-1.53,quarter_front,31)]
            M.grid('interior.upper_quarter_return',rows,plum,flip=s<0)
            box('interior.forward_quarter_card',(s*.884,.610,(-.985+quarter_front)*.5),(.024,.50,quarter_front+.985),plum,.010)
            # The upholstery meets the belt return, closing the thin sky band.
            rows=[]
            for z in np.linspace(-.65,.78,45):
                rows.append([(s*.871,.825,z),(s*.925,.896,z),(s*side_x(.9,z),.9,z)])
            M.grid('interior.upper_door_rail',rows,plum,flip=s<0)
        rows=[]
        for x in np.linspace(-.916,.916,51):
            back=-1.53-.065*(1-(x/.916)**2)
            yback=.919+.008*(1-(x/.916)**2)-.008
            rows.append([(x,.860+(yback-.860)*t,-1.23+(back+1.23)*t) for t in np.linspace(0,1,12)])
        M.grid('interior.parcel_shelf',rows,plum)

    E['interior']=interior

    # Original molded tire-size lettering, kept subtle like raised rubber.
    import io
    from PIL import ImageFont
    tyre_type=Image.new('RGBA',(1024,64),(0,0,0,0));td=ImageDraw.Draw(tyre_type)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',24)
    td.text((32,19),'155/80 R13   RADIAL   155/80 R13   RADIAL',font=font,fill=(76,74,74,255))
    buf=io.BytesIO();tyre_type.save(buf,format='PNG');ti=len(M.images);M.images.append(('tire_sidewall_type',buf.getvalue()))
    tyretype=M.mat('molded_rubber_lettering',0xffffff,.88,0)
    M.materials[tyretype]['pbrMetallicRoughness']['baseColorTexture']={'index':ti}
    M.materials[tyretype].update(alphaMode='MASK',alphaCutoff=.3)
    oldwheel=E['wheel']
    def wheel(i):
        c=oldwheel(i);s=-1 if i%2==0 else 1
        spin=next(j for j,n in enumerate(M.nodes) if n['name']=='wheel_'+str(i)+'_spin')
        steer=next(j for j,n in enumerate(M.nodes) if n['name']=='wheel_'+str(i)+'_steer')
        M.parts[:]=[p for p in M.parts if not (p['parent']==steer and p['name']=='wheel.brake_drum')]
        with parent(steer):
            # The stationary brake lies behind the wire cone. An outboard cap
            # through the cone hides the opposite-hand lacing and is incorrect.
            cylinder('wheel.brake_drum',c+[-s*.100,0,0],c+[-s*.005,0,0],.128,steel,48)
        # Keep the tested tyre envelope, tread, whitewall, independent hub and
        # brake. Replace shallow wire/disc ornament with deeply laced rim planes.
        M.parts[:]=[p for p in M.parts if not (p['parent']==spin and p['name'].startswith(('wheel.wire_spoke','wheel.knockoff','wheel.hub','wheel.inner_barrel','wheel.rim_barrel','wheel.tyre','wheel.tread_sipe')))]
        with parent(spin):
            # Two shallow continuous grooves and staggered tread-block sipes
            # are actual recesses. Outer diameter/contact remain unchanged.
            shoulder=[(-.0775,.178),(-.0775,.215),(-.073,.255),(-.067,.2665714286),(-.059,.282),(-.051,.2857866667)]
            tread_x=sorted(set([*np.linspace(-.044,.044,13),-.0255,-.0185,.0185,.0255]))
            profile=shoulder+[(x,.2891) for x in tread_x]+[(-x,r) for x,r in shoulder[::-1]]
            rows=[]
            angles=[TAU*(period+phase)/32 for period in range(32) for phase in (0,.30,.42,.50,.58,.70)]+[TAU]
            for base_angle in angles:
                row=[]
                for x,r in profile:
                    a=base_angle-TAU*max(-1,min(1,x/.044))*.35/32
                    if abs(x)<=.067:
                        r-=.0040*sum(math.exp(-((x-xg)/.0035)**2) for xg in (-.022,.022))
                        phase=(a/TAU*32+x/.044*.35)%1
                        r-=.0030*math.exp(-((phase-.5)/.10)**2)*(1-smoothstep(.059,.067,abs(x)))
                    row.append(c+[x,r*math.sin(a),r*math.cos(a)])
                rows.append(row)
            M.grid('wheel.tyre',rows,rubber,flip=True)
            for side in (-1,1):
                rows=[];uv=[]
                for a in np.linspace(0,TAU,97):
                    row=[]
                    for r in (.246,.266):
                        xx=float(np.interp(r,[.215,.255,.282],[.0775,.073,.059]))+.0003
                        row.append(c+[side*xx,r*math.sin(a),r*math.cos(a)])
                    rows.append(row);uv.append([(a/TAU,0),(a/TAU,1)])
                M.grid('wheel.molded_sidewall_type',rows,tyretype,uv,flip=side<0)
            for side in (-1,1):
                # Revolved drop-center rim, polished rolled bead and deep dish.
                profile=[(.070,.172),(.073,.166),(.063,.155),(.029,.145),(.015,.137),(-.015,.137),(-.029,.145),(-.063,.155),(-.073,.166),(-.070,.172)]
                if side<0:continue
                rows=[]
                for a in np.linspace(0,TAU,97):rows.append([c+[xx,r*math.sin(a),r*math.cos(a)] for xx,r in profile])
                M.grid('wheel.formed_rim_barrel',rows,chrome,flip=True)
            cylinder('wheel.hub',c+[-.052,0,0],c+[.052,0,0],.039,chrome,40)
            for side in (s,):
                for depth,r in ((.066,.055),(.015,.063)):
                    torus('wheel.spoke_flange',c+[side*depth,0,0],r,.004,chrome,segments=48,sides=7)
                for j in range(48):
                    a=TAU*j/48
                    for phase,hubr,hubx,outerx in ((1.20,.055,.066,.038),(-1.20+math.pi/48,.063,.015,.061)):
                        a2=a+phase
                        p0=c+[side*hubx,hubr*math.sin(a2),hubr*math.cos(a2)];p1=c+[side*outerx,.153*math.sin(a),.153*math.cos(a)]
                        cylinder('wheel.wire_spoke',p0,p1,.00180,chrome,6)
                        # Threaded spoke nipple at the outer end.
                        p2=p1+(p0-p1)*.045;cylinder('wheel.spoke_nipple',p1,p2,.0021,silver,8)
                cylinder('wheel.knockoff_hub',c+[side*.057,0,0],c+[side*.077,0,0],.034,chrome,32,r2=.028)
                torus('wheel.knockoff_rim',c+[side*.076,0,0],.028,.0025,chrome,segments=40,sides=7)
                for a in (0,TAU/3,TAU*2/3):
                    pts=[c+[side*(.075+.006*t),(.021+.035*t)*math.sin(a+.24*t),(.021+.035*t)*math.cos(a+.24*t)] for t in np.linspace(0,1,8)]
                    tube('wheel.knockoff_ear',pts,.0047,chrome,8)
                cylinder('wheel.center_medallion',c+[side*.077,0,0],c+[side*.080,0,0],.018,gold,28)
                # Fine moulded sidewall ribs around the white stripe.
                for r in (.207,.242,.250):torus('wheel.sidewall_ring',c+[side*.075,0,0],r,.0008,rubber,segments=80,sides=5)
        return c
    E['wheel']=wheel
