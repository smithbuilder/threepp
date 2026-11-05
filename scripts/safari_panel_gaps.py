"""Exact convex panel-channel topology, clipped against the rendered skin.

No raised line, alpha decal, centroid deletion or displacement-only shortcut:
each crossing source triangle is partitioned at both real channel boundaries.
The two painted panels remain at the original surface; the channel has a
recessed floor and separate narrow returns at both sheet edges.
"""
import numpy as np


def _offset(loop,distance):
    p=np.asarray(loop,float)
    if np.linalg.norm(p[0]-p[-1])<1e-9:p=p[:-1]
    keep=np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>1e-9];p=p[keep]
    area=np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
    if area<0:p=p[::-1]
    edges=np.roll(p,-1,axis=0)-p;edges/=np.linalg.norm(edges,axis=1)[:,None]
    cross=edges[:,0]*np.roll(edges[:,1],-1)-edges[:,1]*np.roll(edges[:,0],-1)
    if np.min(cross)<-1e-7:raise ValueError('Panel boundary must be convex')
    n=np.c_[-edges[:,1],edges[:,0]];previous=np.roll(n,1,axis=0)
    result=p+distance*(previous+n)/np.maximum(1+np.sum(previous*n,axis=1)[:,None],1e-9)
    return result


def _clip(poly,axis,origin,normal,inside):
    if not poly:return []
    out=[];direction=1 if inside else -1
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        av=float((a[:3][axis]-origin)@normal)*direction
        bv=float((b[:3][axis]-origin)@normal)*direction
        if av>=-1e-10:out.append(a)
        if (av>=-1e-10)!=(bv>=-1e-10):
            t=av/(av-bv);out.append(a+(b-a)*t)
    return out


def _planes(loop):
    edge=np.roll(loop,-1,axis=0)-loop
    edge/=np.linalg.norm(edge,axis=1)[:,None]
    return loop,np.c_[-edge[:,1],edge[:,0]]


def build_panel_gap(model,name,prefix,surface,outline,material,axes,width=.004,depth=.004):
    outer=_offset(outline,-width*.5);inner=_offset(outline,width*.5)
    op,on=_planes(outer);ip,inn=_planes(inner);axis=list(axes)
    lower=outer.min(0);upper=outer.max(0);channel=[];channel_faces=[]
    affected=0
    for index,part in list(enumerate(model.parts)):
        if not part['name'].startswith(prefix):continue
        points=part['p'].astype(float);uv=part['uv'].astype(float);norm=part['n'].astype(float)
        color=part['colors'];attributes=np.c_[points,uv,norm,np.ones((len(points),4)) if color is None else color]
        paint=[];paint_faces=[]
        def emit(poly,target,faces,offset=0.):
            if len(poly)<3:return
            start=len(target)
            for vertex in poly:
                vertex=vertex.copy();n=vertex[5:8];n/=max(np.linalg.norm(n),1e-12)
                vertex[:3]-=n*offset;vertex[5:8]=n;target.append(vertex)
            faces.extend((start,start+i,start+i+1) for i in range(1,len(poly)-1))
        for face in part['f']:
            polygon=[attributes[i] for i in face];q=points[face][:,axis]
            if np.any(q.max(0)<lower) or np.any(q.min(0)>upper):
                emit(polygon,paint,paint_faces);continue
            values=(q[:,None,:]-ip[None,:,:])*inn[None,:,:]
            if np.all(values.sum(2)>=-1e-10):
                emit(polygon,paint,paint_faces);continue
            remaining=polygon
            for origin,normal in zip(op,on):
                emit(_clip(remaining,axis,origin,normal,False),paint,paint_faces)
                remaining=_clip(remaining,axis,origin,normal,True)
                if not remaining:break
            if not remaining:continue
            for origin,normal in zip(ip,inn):
                fragment=_clip(remaining,axis,origin,normal,False)
                if fragment:affected+=len(fragment)
                emit(fragment,channel,channel_faces,depth)
                remaining=_clip(remaining,axis,origin,normal,True)
                if not remaining:break
            emit(remaining,paint,paint_faces)
        array=np.asarray(paint,float)
        # Weld attribute-identical clip corners. Shared positions keep their
        # original interpolated smooth normal and their existing atlas UV.
        _,first,inverse=np.unique(np.round(array,7),axis=0,return_index=True,return_inverse=True)
        array=array[first];faces=inverse[np.asarray(paint_faces)]
        model.mesh(part['name'],array[:,:3],faces,part['mat'],array[:,3:5],
                   None if color is None else array[:,8:12],normals=array[:,5:8])
        model.parts[index]=model.parts.pop()
    if not channel_faces:raise ValueError('Panel channel did not cross skin '+name)
    array=np.asarray(channel,float)
    model.mesh(name+'.recess_floor',array[:,:3],channel_faces,material,array[:,3:5],normals=array[:,5:8])
    for label,loop in [('outer',outer),('inner',inner)]:
        p=[];f=[]
        for q in np.r_[loop,loop[:1]]:
            point,normal=surface.sample(q)
            p.extend((point,point-normal*depth))
        for i in range(len(loop)):
            a=i*2;b=a+2;f.extend(((a,b,a+1),(a+1,b,b+1)))
        if label=='inner':f=[tuple(reversed(t)) for t in f]
        model.mesh(name+'.'+label+'_sheet_return',p,f,material)
    return dict(name=name,width=width,depth=depth,clipped_boundary_vertices=affected)
