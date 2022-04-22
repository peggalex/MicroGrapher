import sympy as sp
import mystic.symbolic as ms
from micrographer import getSolve, parseExpression


x,y,u,PX = sp.symbols('x y u PX')

def getLatexCond(minX, maxX, f, var)->str:
    minX = 0 if minX is None else minX
    s = 'y' if var=='x' else 'x'
    s+='=\\{{'+str(round(minX,13))+'<= '+var
    if maxX is not None:
        s+=' <= '+str(round(maxX,13))
    return s+': '+sp.latex(f)+'\\}}'

def formatCond(minX,maxX,f,var)->dict:

    def getFormattedX(x):
        if x=='\\infty':
            return x
        x = round(x,13)
        if round(x,3)!=x:
            return str(round(x,3))+'...'
        return str(int(x)) if x%1==0 else str(x)
    
    if var=='px':
        form = None
        
        if minX is None:
            minX =  0
        if maxX is None:
            maxX = '\\infty'
            form = '[{}, {})'
        else:
            form = '[{}, {}]'
        minX,maxX = (getFormattedX(x) for x in (minX, maxX))
        func = form.format(minX,maxX)
        return {'func':form.format(minX,maxX),'cond':sp.latex(sp.nsimplify(f))}
    func = sp.latex(sp.nsimplify(f))
    #func = 'x='+func if var=='px' else func
    minX = 0 if minX is None else minX

    cond = '{} \\leq {}'.format(getFormattedX(minX),var)
    if maxX is not None:
        cond+=' \\leq '+getFormattedX(maxX)
    return {'func':func,'cond':cond}

def getConds(minX: float, maxX: float, f, var='x')->list:
    return [getLatexCond(minX,maxX,f,'x' if var=='x' else 'y'),formatCond(minX,maxX,f,var)]

getLatexZeroX = lambda minPx: getConds(minPx,None,0,'px')

def getUParallel(pRatio, arg, py, m):
    _px = pRatio*py
    trueXCoeff = arg.collect(x).coeff(x)
    return trueXCoeff/_px * m

def getDemandCurveMin(f: sp.Min, py, m)->dict:
    
    def getBounds(f: sp.Min)->'bounds':
        mysticIneq = lambda s: ms.simplify(s,variables=['x','y','u'])
        getIneqSolve = lambda solveStr: mysticIneq(mysticIneq(solveStr))
        subIntoStr = lambda eq, var, sub: str(eq).replace(var,'('+str(sub)+')').replace(' ','')
        left,right = f.args
        tanCond = left-right
        ret={}

        for target,other in ((left,right),(right,left)):
            interCond = mysticIneq(str(target)+'<'+str(other))

            if target.has(y):
                tanCondY = getSolve(target-u,y)
            else:
                targetX = getSolve(target-u,x)
                tanCondY = getSolve(tanCond.subs(x,targetX),y)
                
            solve = getIneqSolve(subIntoStr(interCond,'y',tanCondY))
            ret[str(target)]=solve

        return ret
    
    xConds = getBounds(f)
    tanCond = f.args[0]-f.args[1]
    xInter = None
    ret = []
    minX,maxX = (0,m/py)
    minP, maxP = (0,float('inf'))
    
    for arg in f.args:
        if not (arg.has(x) and arg.has(y)):
            continue
        pRatio = getSolve(arg,y).collect(x).coeff(x)*-1
        if pRatio<0:
            continue
        if arg.has(y):
            xCond = xConds[str(arg)]

        _u = getUParallel(pRatio,arg,py,m)
            
        ineqSign = '<' if '<' in xCond else '>'
        xLimU = sp.sympify(xCond.split(ineqSign)[1])
        xLim = xLimU.subs(u,_u)
        
        if ineqSign == '<':
            maxP = pRatio*py
            minX = xLim
            ret.append(getConds(0,xLim,pRatio*py))
            
        else:
            minP = pRatio*py
            maxX = xLim
            xInter = getSolve(arg.subs(y,0)-_u,x)
            ret.append(getConds(xLim,xInter,pRatio*py))
       
    tanCondY = getSolve(tanCond,y)
    bl = PX*x+py*y-m
    tanFunc = getSolve(bl.subs(y,tanCondY),PX)
    ret.append(getConds(minX,maxX, tanFunc))

    if xInter is None:
        ret.append(getConds(maxX,None,0))
    if (minP!=0):
        ret.append(getConds(m/minP,None,m/x))
    if maxP!=float('inf'):
        ret.append(getLatexZeroX(maxP))

    axis_max = max(x for x in (maxP,maxX,xInter) if not (x in (float('inf'),None)))
    return {'latexs':ret, 'axis_max':str(axis_max)}

def getDemandCurvePoly(f, py,m):
    mux,muy = (sp.diff(f,v) for v in (x,y))
    xInter = None
    yInter = None
    ret = []

    from sympy.logic.boolalg import BooleanFalse
    if (type(f.subs(y,0)>0) != BooleanFalse):
        #if there's an x intercept
        for var in (x,y):
            tanCond = mux/muy - PX/py
            _px = getSolve(tanCond.subs(y,0),PX)
            _var = getSolve(_px*x-m,var)
            if _var:
                if var==x:
                    xInter = _var
                    ret.append(getConds(xInter,None,m/x))
                else:
                    yInter = _var


    _x = None
    if any(mu.has(y) for mu in (mux,muy)):
        _y = getSolve(mux/muy - PX/py,y) #isolate y in tan
        _x = getSolve(PX*x+py*_y-m,PX) #sub this y into bl, solve for px
    else:
        _x = getSolve(mux/muy - PX/py,PX) #if there's no y in tan, simply solve for px

    ret.append(getConds(0,xInter, _x))
    if _x.subs(x,0).is_real:
        ret.append(getLatexZeroX(_x.subs(x,0)))

    axis_max = str(max((i for i in (xInter,yInter) if i))) if any((xInter,yInter)) else None 
    return {'latexs':ret, 'axis_max':axis_max}

def getDemandCurveLin(f, py, m):
    ret = []
    pRatio = getSolve(f,y).collect(x).coeff(x)*-1
    _u = getUParallel(pRatio, f, py, m)
    xInter = getSolve((f-_u).subs(y,0),x)
    onLinePX = pRatio*py

    ret.append(getConds(0,xInter,onLinePX))
    ret.append(getConds(xInter,None,m/x))
    ret.append(getLatexZeroX(onLinePX))
    axis_max = str(max(xInter,onLinePX))
    return {'latexs':ret, 'axis_max':axis_max}

def getDemandCurve(exp:str, py=2, m=36)->dict:
    f = sp.sympify(str(parseExpression(exp)),locals={'x':x,'y':y})
    if any(str(fs) not in 'xy' for fs in f.free_symbols): #if there's an invalid variable like z
        raise ValueError('unexpected symbol')
    if type(f) in (sp.Min,sp.Max):
        func = getDemandCurveMin
    elif any(mu.has(x,y) for mu in (sp.diff(f,v) for v in (x,y))):
        func = getDemandCurvePoly
    else:
        func = getDemandCurveLin
    return func(f,py,m)

    
