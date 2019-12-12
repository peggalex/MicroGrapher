import re, math
import sympy as sp

variables = "xy"
x,y,M,C,U,PX = sp.symbols('x y m c u px',nonnegative=True, real=True)


class MinMaxError(Exception):

    def __str__(self):
        return 'Invalid min or max function'
    

def parseExpression(s: str, evaluate=True)->sp.expr:
    #evaluate param so that I can leave 2 as 2 instead of 2.0, etc

    varGroup = "(:?{})".format("|".join(variables))
    digitGroup = "(:?\\d|\\.)"
    # sp will evaluate if the number of decimal points
    # match up so the digit non-capture group can be trivial
    
    numberByVar = "({}{})".format(digitGroup,varGroup)
    varByNumber = "({}{})".format(varGroup,digitGroup)
    varByVar = "({})".format(varGroup)+"{2}"
    numberVarByBracket = "(({}|{})\\()".format(varGroup,digitGroup)
    bracketByNumberVar = "(\\)({}|{}))".format(varGroup,digitGroup)
    bracketByBracket = "(\\)\\()"
    minMaxRegex = "((?:min)|(?:max))\\((.+),(.+)\\)"

    if any(m in s for m in ('min','max')):
        m = re.fullmatch(minMaxRegex,s)
        if not m and sum(s.count(m) for m in ('min','max'))==1:
            raise MinMaxError('min max functions must be limited to'+
                'the format Min/Max(<>,<>), without nested min/maxes')
        
        minMax,arg0,arg1 = m.groups()
        func = sp.Min if minMax == 'min' else sp.Max
        convert = lambda f: sp.sympify(parseExpression(f, evaluate),locals={'x':x,'y':y})
        return sp.sympify(func(convert(arg0),convert(arg1)))


    for expr in (numberByVar,varByNumber,varByVar,
        numberVarByBracket,bracketByNumberVar,bracketByBracket):

        m = re.search(expr,s)
        while m:
            index = s.find(m.group())
            s = s[:index+1]+"*"+s[index+1:]
            # add in a multiplication operator so
            # sp knows xy = x*y, 2(x+1) = 2*(x+1)
            m = re.search(expr,s)

    s = s.replace('m','M')
    #sp only reads min/max functions if capitalized
    s = s.replace("Max*","max")
    #max ends with an x, which is the same as the x variable

    ret = sp.sympify(s,locals={'x':x,'y':y})
    return ret.evalf() if evaluate else ret

def getFunctionType(exp: sp.expr)->str:
    numberPattern  = "(?:-?(?:\\d+|\\.\\d+|\\d+\\.\\d+))"
    
    polynomialPattern = "({}\\*)?x(?:\\*\\*({}))?([\\+\\*])({}\\*)?y(?:\\*\\*({}))?".format(*((numberPattern,)*4))

    groupKeys = ['xCoeff','xExpo','sign','yCoeff','yExpo']
    reGroupToDic = lambda gs: {groupKeys[i]:gs[i] for i in range(len(gs))}

    if exp.has(sp.Min):
        return 'perfect complements' if exp.has(sp.Min(y,x)) else 'complements'
    
    sympyStr = str(exp.evalf()).replace(' ','')
    m = re.fullmatch(polynomialPattern,sympyStr)
    if not m:
        #raise ValueError
        return ''

    dic = reGroupToDic(m.groups())

    getNum = lambda s: 1 if s is None else float(s)
    if dic['sign']=='+':

        if all(getNum(dic[v+'Expo'])==1 for v in 'xy'):
            return 'perfect substitutes'
            
        elif any(getNum(dic[v+'Expo'])==1 for v in 'xy'):
            expo = dic['xExpo'] if getNum(dic['xExpo'])!=1 else dic['yExpo']
            return 'function type: quasi-linear' if float(expo)<1 else ''
            
        else:
            # function is x^a + y^b for a,b=/=0
            return ''
    elif dic['sign']=='*':
        return 'cobb douglas'

    
'''
def getMultiVariableSolve(funcs, subs, *varis)->sp.expr:

    solve = sp.solve(funcs,*varis)
    if type(solve)!=list:
        return solve
    if solve:
        from sympy.logic.boolalg import BooleanFalse
        if type(solve[0])==dict:
            for f in solve:
                try:
                    if all(sp.solve(v>0) is not BooleanFalse for v in f.values()):
                        return f
                except Exception:
                    continue
        else:
            for e in solve:
                try:
                    if type(e)==tuple:
                        if all(type(sp.solve(f.subs(subs)>0)) is not BooleanFalse for f in e):
                            return {varis[i]:e[i] for i in range(len(varis))}
                    else:
                        if type(sp.solve(e.subs(subs)>0)) is not BooleanFalse:
                            return e
                except Exception:
                    continue
    return None
'''

def getSolve(funcs: 'list[sp.exp] or sp.exp', *varis)->sp.expr:
    #sympy is terrible
    
    solve = sp.solve(funcs,*varis)
    if type(solve)!=list:
        return solve
    if solve:
        from sympy.logic.boolalg import BooleanFalse
        if type(solve[0])==dict:
            for f in solve:
                try:
                    if all(sp.solve(v>0) is not BooleanFalse for v in f.values()):
                        return f
                except Exception:
                    continue
        else:
            for e in solve:
                try:
                    if type(e)==tuple:
                        if all(len(f.free_symbols)>1 or type(sp.solve(f>0)) is not BooleanFalse for f in e):
                            return {varis[i]:e[i] for i in range(len(varis))}
                    else:
                        if len(e.free_symbols)>1 or type(sp.solve(e>0)) is not BooleanFalse:
                            return e
                except Exception:
                    continue
    return None

    
def isMinMax(exp)->bool:
    for weirdF in (sp.Min,sp.Max):
        if type(exp)==weirdF:
            return weirdF
    return None

def getMinMaxTanCond(exp)->sp.expr:
    assert(isMinMax(exp))
    args = tuple(exp._argset)
    return (args[0]-args[1]).evalf()


class Bundle:

    def __init__(self,exp: sp.expr, px: int, py: int, m:int):
        self.px, self.py, self.m, self.exp = px, py, m, exp
        self.bl = (px*x+py*y-m).evalf()
        self.uCurve = self.getUCurve()

    def getUCurve(self)->'UtilityCurve':
    #factory for UtilityCurve objects
               
        exp,px,py,m,bl = self.exp, self.px, self.py, self.m, self.bl

        dicToTup = lambda d: (d[x],d[y])
        tupToDic = lambda t: {x:t[0],y:t[1]}
        #dicts are unhashable but i want them as keys

        getInter = lambda var,otherVar: getSolve(self.bl.subs(otherVar,0),var)
        xInter,yInter = (getInter(v,ov) for v,ov in ((x,y),(y,x)))

        zeroCondX, zeroCondY = (0,yInter), (xInter,0)

        curvesDic = {zeroCondX: EdgeCaseUtility(self,x),
                zeroCondY: EdgeCaseUtility(self,y)}

        hasDiff = lambda f: any(sp.diff(f,v).has(x,y) for v in (x,y))

        if isMinMax(exp):
            uCurve = MinMaxUtility(self)
            curvesDic[dicToTup(uCurve.getPoint())] = uCurve

        elif any(hasDiff(f) for f in (exp,bl)):
            uCurve = TangentUtility(self)
            if uCurve.getPoint() and all(v in uCurve.getPoint().keys() for v in (x,y)):
                #(1+x)(1+y) etc. can return negative solutions that are
                #dismissed by assumption, so getpoint is none
                curvesDic[dicToTup(uCurve.getPoint())] = uCurve

        return curvesDic[max(curvesDic.keys(),key=lambda t:exp.evalf(subs=tupToDic(t)))]

class UtilityCurve:
# abstract class

    def __init__(self, bundle: Bundle):
        self.bundle = bundle
        self.isEdgeCase = False

    # func prototype
    def getTanCond(self)->sp.expr:
        pass

    # func prototype
    def getPoint(self)->'{x:<>,y:<>}':
        pass
    
    def getUtility(self,simplify=False)->float:
        return self.bundle.exp.evalf(subs=self.getPoint())

    def getCurve(self)->sp.expr:
        return (self.bundle.exp-self.getUtility()).evalf()

class TangentUtility(UtilityCurve):

    def __init__(self, bundle: Bundle):
        super().__init__(bundle)
        mux,muy = sp.diff(bundle.exp,x), sp.diff(bundle.exp,y)

    #@Override
    def getTanCond(self)->sp.expr:
        mux,muy = (sp.diff(self.bundle.exp,var) for var in (x,y))
        mrs = mux/muy
        #pRatio = self.bundle.px/self.bundle.py
        bl_dx, bl_dy = (sp.diff(self.bundle.bl,var) for var in (x,y))
        pRatio = bl_dx/bl_dy
        return (mrs-pRatio).evalf()

    #@Override
    def getPoint(self)->'{x:<>,y:<>}':
        return getSolve([self.getTanCond(),self.bundle.bl])

class MinMaxUtility(TangentUtility):
# want to inherhit TangentUtility getCurveJSONs incase
# the min/max function has a tangent curve arg
    
    def __init__(self, bundle: Bundle):
        super().__init__(bundle)
        self.left, self.right = tuple(bundle.exp._argset)

    #@Override
    def getTanCond(self)->sp.expr:
        return (self.left-self.right).evalf()

class EdgeCaseUtility(UtilityCurve):

    def __init__(self, bundle: Bundle, zeroVariable: sp.Symbol):
        super().__init__(bundle)
        self.zeroVariable = zeroVariable

    #@Override
    def getPoint(self)->'{x:<>,y:<>}':
        otherVariable = x if self.zeroVariable==y else y
        blWithoutZero = self.bundle.bl.subs(self.zeroVariable,0)
        otherVariableSol = getSolve(blWithoutZero,otherVariable)
        return {self.zeroVariable: 0, otherVariable: otherVariableSol}

class BundleSE:

    def __init__(self, exp, oldBundle, newBundle):
        self.exp = exp
        self.oldBundle, self.newBundle = oldBundle, newBundle
        self.budget = newBundle.px*x+newBundle.py*y-M

        self.hicksBundle = self.getHicksBundle()
        self.slutsBundle = self.getSlutsBundle()

    def getEdgeCaseIncome(self)->float:
        incomes = []
        uCurveA = self.oldBundle.uCurve.getCurve()
        u = self.oldBundle.uCurve.getUtility()
        
        for var,otherVar in ((x,y),(y,x)):
            varSubZero = uCurveA.subs(var,0)
            if not varSubZero.has(otherVar):
                continue
            otherVarVal = getSolve(varSubZero,otherVar)
            if otherVarVal:
                sub = {var:0,otherVar:otherVarVal}
                if isMinMax(self.exp):
                    subU = self.exp.subs(sub)
                    if subU!=u:
                        continue
                    
                income = getSolve(self.budget.subs(sub),M)
                incomes.append(income)
                
        return incomes

    def getMinMaxIncome(self)->float:
        incomes = []
        u = self.oldBundle.uCurve.getUtility()
        
        tanPoint = getSolve([self.exp.args[0]-u,self.exp.args[1]-u])
        if tanPoint:
            incomes.append(getSolve(self.budget.subs(tanPoint),M))

        return incomes

    def getTanIncome(self)->float:
        incomes = []
        uCurveA =self.oldBundle.uCurve.getCurve()
        
        getDxDy = lambda f: [sp.diff(f,v) for v in (x,y)]
        (mux,muy),(bl_dx,bl_dy) = [getDxDy(f) for f in (self.exp,self.budget)]

        if any(df.has(x,y) for df in (mux,muy,bl_dx,bl_dy)):
            tanCond = (mux/muy-bl_dx/bl_dy).evalf()
            tanSolve = getSolve([uCurveA,tanCond])
            if tanSolve:
                income = getSolve(self.budget.subs(tanSolve),M)
                incomes.append(income)

        return incomes
            

    def getHicksBundle(self)->Bundle:
        possibleIncomes = []

        possibleIncomes.extend(self.getEdgeCaseIncome())

        if isMinMax(self.exp):
            possibleIncomes.extend(self.getMinMaxIncome())
        else:
            possibleIncomes.extend(self.getTanIncome())
            
        hicksIncome = min(possibleIncomes, key=lambda m: (m-self.newBundle.m))
        return Bundle(self.exp, self.newBundle.px, self.newBundle.py, hicksIncome)


    def getSlutsBundle(self):
        tanPoint = self.oldBundle.uCurve.getPoint()
        slutsIncome = getSolve(self.budget.subs(tanPoint),M)
        return Bundle(self.exp,self.newBundle.px,self.newBundle.py,slutsIncome)


BundleA=None
BundleB=None
BundleC=None
BundleD=None
BundleE=None


def run(equation:str,px:str,px2:str,py:str,m:float,width:int =10):
    global BundleA,BundleB,BundleC,BundleD,BundleE

    px,px2,py = (parseExpression(v) for v in (px,px2,py))

    from sympy.core.sympify import SympifyError
    try:       
        exp = parseExpression(equation)
    except SympifyError:
        print("error: invalid expression: {}. Check brackets and decimals".format(equation))
        return 1
    except MinMaxError:
        print("error: invalid use of min and max in {}. Make sure there's at most 1 min/max, and that it is the only term".format(equation))
        return 1

    if any(str(fs) not in variables for fs in exp.free_symbols): #if there's an invalid variable like z
        print("error: invalid variables in {}. Don't include sin, ln, nested min/max, or variables other than x/y etc".format(equation))
        return 1
    
    print("evaluated output: {}".format(exp))
    print(exp)

    BundleA = Bundle(exp,px,py,m)
    print('finished bundle A')
    BundleC = Bundle(exp,px2,py,m)
    print('finished bundle C')
    se = BundleSE(exp,BundleA,BundleC)
    print('finished B,D')
    BundleE = BundleSE(exp,BundleC,BundleA).hicksBundle
    print('finished curves')
    BundleB, BundleD = se.hicksBundle, se.slutsBundle
    bundles = {'a':BundleA,'c':BundleC,
        'b':BundleB, 'd':BundleD, 'e':BundleE}

    def simpNum(exp):
        if float(exp)%1==0:
            return None
        
        simpExp = sp.nsimplify(exp, rational=False)
        if type(simpExp) == sp.sqrt or\
                any(type(a) in (sp.sqrt,sp.Pow) for a in simpExp.args):
            return sp.latex(simpExp)
        elif str(sp.sympify(exp))!=str(simpExp):
            s = str(int(simpExp)) if simpExp>1 else ''
            return s+sp.latex(sp.nsimplify(simpExp%1))
        else:
            return None

    simp = lambda exp: sp.latex(sp.nsimplify(exp))
        
    truncZeros = lambda num: str(int(num)) if num%1==0 else str(float(num))
    dicToLst = lambda dic: [truncZeros(c) for c in (dic[x],dic[y])]

    simpCoord = lambda coord: [simpNum(s) for s in coord]

    padding = 0.25
    
    pointsJSON = {k:dicToLst(b.uCurve.getPoint()) for k,b in bundles.items()}
    pointsSimpJSON = {k+'_simp':simpCoord(c) for k,c in pointsJSON.items()}
    
    def getPointsLine(func):
        tups = []

        for var in (x,y):
            notVar = y if var==x else x
            intercept = getSolve(func.subs(notVar,0),var)
            point = {x:None,y:None}
            
            if intercept>axis_length:
                point[var] = axis_length
                point[notVar] = getSolve(func.subs(var,axis_length),notVar)

            else:
                point[var] = intercept
                point[notVar] = 0
                
            tups.append([str(point[v]) for v in (x,y)])
        return tups

    print('finished curves bit')

    uToJSON = lambda u: {'func':simp(parseExpression(equation,False))+'=u','u':str(u),'u_simp':simpNum(u)}
    mToJSON = lambda b: {'func':simp(b.px*x+b.py*y)+'=m','m':str(b.m), 'm_simp':simpNum(b.m)}

    curvesJSON = {k+"_curve": uToJSON(b.uCurve.getUtility()) for k,b in bundles.items()}

    '''lines = {k+'_bl':getFuncJSON(getSolve(b.bl,y),const = {'m':b.m}) for
             k,b in bundles.items()}'''

    linesJSON = {k+'_bl':mToJSON(b) for k,b in bundles.items()}

    tanJSON = {}
    for k,b in bundles.items():
        if type(b.uCurve)==EdgeCaseUtility:
            tan = str(b.uCurve.zeroVariable)+'=0'         
        else:
            tanCond = b.uCurve.getTanCond()
            isoVar = y if tanCond.has(y) else x
            tan = str(simp(getSolve(b.uCurve.getTanCond(),isoVar)))+'='+str(isoVar)
        tanJSON[k+'_tan'] = tan
    
    retDic = {**curvesJSON,**linesJSON,**pointsJSON, **tanJSON, **pointsSimpJSON}

    retDic['LoV'] = simp(getSolve(getMinMaxTanCond(exp),y))+'=y' if isMinMax(exp) else ''
    # solve in terms of y and then do +'=y'
    # because 'x'+'=y' looks better than 'x-y'+'=0'

    max_points = lambda v: max(float(c[0 if v==x else 1]) for c in pointsJSON.values())
    max_inter = lambda v,: max(getSolve((_px*x+py*y-m).subs(y if v==x else x,0),v) for _px in (px,px2))

    for v in (x,y):
        retDic['axis_max_'+str(v)] = str(max(max_points(v),max_inter(v)))
        
    retDic['funcType'] = getFunctionType(exp)
    print(retDic)
    return retDic

def runBasic(exp: str):
    return run(exp,'4','1','2',36)

testBasic = lambda: run('xy','4','1','2',36)

            

        






