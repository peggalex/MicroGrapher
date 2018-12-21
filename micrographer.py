import re, turtle, sympy

class Operators:
    _precedence = 0
    _function = lambda x,y: None
    _strings = ('')
    _isLeftAssociative = False
    #left associative means that the operation is not
    # associative, so that the order is important
    #ie x/y =/= y/x for some x,y and
    # x-y =/= y-x

    def getPrecedence(self):
        return self._precedence

    def execute(self,a,b):
        return type(self)._function(a,b)

    def checkString(self,c: 'char'):
        return c in self._strings

    def getString(self):
        return self._strings

    def isLeftAssociative(self):
        return self._isLeftAssociative

    def __str__(self):
        return self._strings[0]

    #ideally, these would not have self in them,
    #as these are all static methods.
    #However, static attributes in python suck,
    #so i'd have to say Operator._precedence etc
    #which means my child classes would need to override

class Add(Operators):
    _precedence = 1
    _function = lambda x,y:x+y
    _strings = ("+")
    _isLeftAssociative = True


class Subtract(Operators):
    _precedence = 1
    _function = lambda x,y:x-y
    _strings = ("-")
    _isLeftAssociative = True

class Multiply(Operators):
    _precedence = 2
    _function = lambda x,y:x*y
    _strings = ("*")
    _isLeftAssociative = True

class Divide(Operators):
    _precedence = 2
    _function = lambda x,y:x/y
    _strings = ("/")
    _isLeftAssociative = True

class Exponent(Operators):
    _precedence = 3
    _function = lambda x,y:x**y
    _strings = ("^")
    _isLeftAssociative = False


Operators = (Add(),Subtract(),Multiply(),Divide(),Exponent())
#global constant
class OperatorHandlers:
    
    def getOperator(c: 'char'):
        for operator in Operators:
            if operator.checkString(c):
                return operator
            
        return None

class Stack:

    def __init__(self):
        self._items = []

    def pop(self):
        assert(self._items)
        return self._items.pop()

    def _peek(self, index):
        return self._items[index] if self._items else None

    def peek(self):
        return self._peek(-1)

    def isEmpty(self):
        return not self._items

    def push(self, item):
        self._items.append(item)

    #@override
    def __repr__(self):
        s=''
        for e in self._items:
            s+=str(e)+","
        return s.strip(",")

    def getItems(self)->list:
        return self._items

class Queue(Stack):

    def __init__(self):
        super().__init__()

    #@override
    def pop(self):
        assert(self._items)
        return self._items.pop(0)

    #@override
    def peek(self):
        return self._peek(0)


multiply = lambda x,y: x*y
divide = lambda x,y: x/y
add = lambda x,y: x+y
subtract = lambda x,y: x-y  
toPower = lambda x,y: x**y

operatorDic = {('x','*'):{'func':multiply}, ('/'): divide,\
               ('+'):add, ('-'):subtract, ('^'):toPower}


variables = ""
digitRegex = "(-?(\\d+|\\.\\d+|\\d+\\.\\d+))"
_operandRegexS = digitRegex.strip(")")+"|({}?".format(digitRegex)+"({}))+))"

operatorRegexS = "("
for operator in Operators:
    for c in operator.getString():
        operatorRegexS += "{}|".format("\\"+c)
operatorRegexS = operatorRegexS.strip("|")
operatorRegexS += ")"

#ideally, we would make these brackets into 
#non capture groups

def getBracket(s)->str:
    numOpen = 0
    for i in range(len(s)):
        if s[i]=="(":
            numOpen+=1
        elif s[i]==")":
            if numOpen==0:
                #print(s[:i])
                return s[:i]
            else:
                numOpen-=1
    return ''

def evaluateBrackets(s):
    finalExp = ''
    i=0

    while i<len(s):
        if s[i]!="(":
            finalExp+=s[i]
            i+=1
            continue

        bracket = getBracket(s[i+1:])
        
        if not bracket:
            return False
        
        elif not evaluateBrackets(bracket):
            return False

        if variables:
            finalExp += variables[0]
        else:
            finalExp += '0'
        #if the nested brackets are valid, we know that the bracket will return an
        #equation that can be evaluated. So make it zero for regex

        i = i+len(bracket)+2
        #plus 2 to skip the closing bracket

    #print('final s: {}, works? {}'.format(finalExp,re.fullmatch(regexEquation,finalExp)))
    return re.fullmatch(regexEquation,finalExp) is not None

def convert(s: str)->list:
    operator = Stack()
    output = Queue()
    tokens = Stack()
    for c in s[::-1]:
        tokens.push(c)

    lastCharOperator = True

    while not tokens.isEmpty():
        c = tokens.pop()
        #print(c)

        if c.isdigit() or c=='.' or (c=='-' and lastCharOperator):
            num = c
            while not tokens.isEmpty():
                c = tokens.peek()
                if c.isdigit() or c=='.':
                    assert(num.count('.')<=1)   #this shoulda been tested with the regex
                    num += tokens.pop()
                else:
                    break

            if num is "-":
                tokens.push("*")
                tokens.push("1")
                tokens.push("-")    # -y should be -1 * y or -(1+y) etc
            else:                
                output.push(float(num)) if float(num)%1!=0 else output.push(int(num))              
                lastCharOperator = False

            
        elif c=="(" or c in variables:
            if not lastCharOperator:
                tokens.push(c)
                tokens.push("*")
                # if we have 2(...), should be interpreted
                # as 2*(...). Same with xyz ~ x*y*z
                
            else:
                if c in variables:
                    output.push(c)
                    lastCharOperator = False
                else:
                    operator.push(c)
                
        elif c==")":
            while not operator.peek()=="(":
                output.push(operator.pop())
            operator.pop()
        else:
            opObj = OperatorHandlers.getOperator(c)
            assert(opObj is not None)
            precedence = opObj.getPrecedence()

            topStack = operator.peek()
            
            while topStack is not None and topStack!= "(" and\
                (topStack.getPrecedence() > precedence or\
                (topStack.getPrecedence() == precedence and\
                 topStack.isLeftAssociative()) ):
                #verbose i know

                output.push(operator.pop())
                topStack = operator.peek()
     
            operator.push(opObj)
            lastCharOperator = True

    while not operator.isEmpty():
        output.push(operator.pop())

    return output.getItems()

class ItsTreesonThen:

    def __init__(self,value, left=None, right=None):
        self._value = value
        self._left = left
        self._right = right

    def getLeft(self):
        return self._left

    def getRight(self):
        return self._right

    def setLeft(self, l):
        self._left = l

    def setRight(self, r):
        self._right = r

    def getValue(self):
        return self._value

    def getDepth(self):
        left, right = self.getLeft(),self.getRight()
        leftNum, rightNum = int(bool(left)),int(bool(right))
        
        if type(left) == ItsTreesonThen:
            leftNum += left.getDepth()
        if type(right) == ItsTreesonThen:
            rightNum += right.getDepth()

        return max(leftNum,rightNum)

    def __str__(self):
        s = "value: {}".format(self._value)
        s += "\n\t left: {}".format(self._left)
        s += "\n\t right: {}".format(self._right)
        print(s)

    #@Global
    def printTree(tree,equation=None,exp=None):
        turtle.clearscreen()
        fontHeight = 12
        font = ('Arial',fontHeight,'normal')
        t = turtle.Turtle(visible=False)
        t.speed('fastest')
        x,y = turtle.screensize()[0]*1.5,turtle.screensize()[1]*1.5
        depth = tree.getDepth()
        length = x//(2**(depth-1))
        height = y//depth
        t.penup()
        if equation and exp:
            t.setpos(-300,-270)
            s = "{} -> {}".format(equation,exp)
            t.write(s,font=font)
        t.setpos(0,y//2)
            
            

        def _printTree(tree,turt=t,size=x):
            if tree.getLeft():
                left = turtle.Turtle(visible=False)
                left.speed('fastest')
                left.penup()
                left.setpos(turt.xcor(),turt.ycor())
                
                left.pendown()
                left.setpos(turt.xcor()-size//4,turt.ycor()-height)#minus size//4
                _printTree(tree.getLeft(),left,size//2)
                
            if tree.getRight():
                right = turtle.Turtle(visible=False)
                right.speed(speed='fastest')
                right.penup()
                right.setpos(turt.xcor(),turt.ycor())
                
                right.pendown()
                right.setpos(turt.xcor()+size//4,turt.ycor()-height)#plus size//4
                _printTree(tree.getRight(),right,size//2)
                
            x1 = turt.xcor()
            turt.penup()
            turt.setpos(x1,turt.ycor()-fontHeight//2)
            turt.write(str(tree.getValue()),align='center',move=True,font=font)
            x2 = turt.xcor()
            radius = max(10,2*(x2-x1))
            turt.seth(90)
            turt.setpos(x1+radius,turt.ycor()+fontHeight//2)
            turt.fillcolor('white')
            
            turt.pendown()
            turt.begin_fill()
            turt.circle(radius)
            turt.end_fill()
            turt.penup()

            turt.setpos(x1,turt.ycor()-fontHeight//2)
            turt.write(str(tree.getValue()),align='center',move=False,font=font)
                
        _printTree(tree,t,x)
                


def buildTree(output: list)->ItsTreesonThen:
    if not output:
        return None

    value = output.pop()
    tree = ItsTreesonThen(value)
    
    if not all(type(value)!=type(o) for o in Operators):
        right = buildTree(output)
        left = buildTree(output) #note, theyre using the same output object that is getting popped
        tree.setLeft(left)
        tree.setRight(right)
        
    return tree

def getExp(tree):
    if not tree:
        return
    
    variables = {c:sympy.symbols(c) for c in 'xyz'}

    def preorder(node):
        if node.getLeft():
            assert(bool(node.getRight()))
            left = preorder(node.getLeft())
            right = preorder(node.getRight())
            return node.getValue().execute(left,right)
            
        else:
            v = node.getValue()
            if str(v) in 'xyz':
                return variables[v]
            else:
                assert(type(v)==int or type(v)==float)
                return v

    return preorder(tree)

class Bundle:

    def __init__(self,exp, px, py, m):
        self.exp = exp
        self.px, self.py, self.m = px, py, m
        self.tanCond = None
        self.bundle = self.getBundle()
        self.uCurve = Bundle.getUtility(self.bundle,self.exp)

    def getBundle(self):
        exp,px,py,m = self.exp, self.px, self.py, self.m
        x,y = sympy.symbols('x y')
        bl = (x*px+y*py-m).evalf()

        mux,muy = sympy.diff(exp,x), sympy.diff(exp,y)
        isFunctionXY = lambda f: any("Symbol('{}')".format(v) in sympy.srepr(f) for v in ('x','y'))

        #if we can solve with tan mrs=pRatio:
        if isFunctionXY(mux) or isFunctionXY(muy):
            print("\tmux = {}".format(mux))
            print("\tmuy = {}".format(muy))
        
            mrs = sympy.simplify(sympy.diff(exp,x)/sympy.diff(exp,y))
            print('\tMRS: {}'.format(mrs))
        
            pRatio = px/py
            print('\tprice ratio: {}'.format(pRatio))

            if isFunctionXY(mux):
                self.tanCond = (sympy.solve(mrs-pRatio,x)[0]-x).evalf()
            else:
                self.tanCond = (sympy.solve(mrs-pRatio,y)[0]-y).evalf()
            print('\ttangency condition [MRS = price ratio] => {} = 0'.format(tanCond))              

            sysOfEq = [tanCond, bl]
            A,b = sympy.linear_eq_to_matrix(sysOfEq, x, y)
            
            assert(tuple(sympy.linsolve((A,b), [x,y])))
            bundleA = tuple(sympy.linsolve((A,b), [x,y]))[0]
            print('substitute in => (x,y) = {}'.format(bundleA))
        else:
            maxU = lambda t: exp.evalf(subs={x:t[0],y:t[1]})
            bundleA = max( ((m/px,0),(0,m/py)) , key=maxU)
            print('substitute in => (x,y) = {}'.format(bundleA))

            self.tanCond = None
             
        return bundleA

    #@global
    def getUtility(tup: tuple, exp):
        u = exp.evalf(subs={x:tup[0],y:tup[1]})
        return (exp-u).evalf()


class BundleSE(bundle):

    def __init__(self, exp, uCurve,px,py):
        self.exp = exp
        self.uCurve = uCurve
        self.px, self.py = px, py

    def getCurveShift(self)
        self.uCurve 
    
        



while(True):
    '''
    variablesS = input('type variables (just press enter for none): ')
    
    if not all(OperatorHandlers.getOperator(c)==None for c in variablesS):
        print("error: variables cannot be operator characters")
        continue
        #using `all` means that I don't have to iterate with a for-loop,
        #so I can use continue to restart the whole process instead of
        #continuing just the nested for-loop

    '''
    variablesS = "xyz"
    variables = ""
    for c in variablesS:
        variables+=c+"|"
    variables = variables.strip("|")

    operandRegexS = _operandRegexS.format(variables)
    regexEquation = re.compile("{}({}{})*".format(operandRegexS,operatorRegexS,operandRegexS))
    
    equation = input('type utility function: ')
    checkNum = re.compile(digitRegex)

    dic = {'px':{'text':'price of good x in period 1','var':None},\
          'px2':{'text':'price of good x in period 2','var':None},\
           'py':{'text':'price of good y','var':None},\
            'm':{'text':'income','var':None}}

    for k in list(dic.keys()):
        while(True):
            var = input('\ttype {}: '.format(dic[k]['text']))
            if re.fullmatch(checkNum,var):
                dic[k]['var']  = float(var)
                break
    px,py,m = dic['px']['var'],dic['py']['var'],dic['m']['var']

        
    if equation == "quit":
        break
    
    if not evaluateBrackets(equation):
        print("error: invalid string, make sure brackets match"+
        " and don't use functions like sin, ln or min/max")
    else:
        output = convert(equation)
        print("\toutput: "+",".join((str(e) for e in output)))
        t=buildTree(output.copy())
        exp = getExp(t).evalf()
        print("evaluated output: {}".format(exp))
        ItsTreesonThen.printTree(t,equation,exp)

        bundleA = Bundle(exp,px,py,m)
        bundleC = Bundle(exp,px2,py,m)
        
        '''
        bundleA = []
        x,y = sympy.symbols('x y')
        bl = (x*px+y*py-m).evalf()

        mux,muy = sympy.diff(exp,x), sympy.diff(exp,y)
        isFunctionXY = lambda f: any("Symbol('{}')".format(v) in sympy.srepr(f) for v in ('x','y'))

        #if we can solve with tan mrs=pRatio:
        if isFunctionXY(mux) or isFunctionXY(muy):
            print("\tmux = {}".format(mux))
            print("\tmuy = {}".format(muy))
        
            mrs = sympy.simplify(sympy.diff(exp,x)/sympy.diff(exp,y))
            print('\tMRS: {}'.format(mrs))
        
            pRatio = px/py
            print('\tprice ratio: {}'.format(pRatio))

            if isFunctionXY(mux):
                tanCond = (sympy.solve(mrs-pRatio,x)[0]-x).evalf()
            else:
                tanCond = (sympy.solve(mrs-pRatio,y)[0]-y).evalf()
            print('\ttangency condition [MRS = price ratio] => {} = 0'.format(tanCond))              

            sysOfEq = [tanCond, bl]
            A,b = sympy.linear_eq_to_matrix(sysOfEq, x, y)
            
            assert(tuple(sympy.linsolve((A,b), [x,y])))
            bundleA = tuple(sympy.linsolve((A,b), [x,y]))[0]
            print('substitute in => (x,y) = {}'.format(bundleA))
        else:
            maxU = lambda t: exp.evalf(subs={x:t[0],y:t[1]})
            bundleA = max( ((m/px,0),(0,m/py)) , key=maxU)
            print('substitute in => (x,y) = {}'.format(bundleA))
            
        u = exp.evalf(subs={x:bundleA[0],y:bundleA[1]})
        uCurveA = (exp-u).evalf()
        '''
            
        '''
        _lambda = sympy.symbols('_lambda')
        bl = (x*px+y*py-m).evalf()
        d = sympy.diff
        sysOfEq = [d(exp,x) - _lambda*d(bl,x),\
                   d(exp,y) - _lambda*d(bl,y),\
                   bl]
        A,b = sympy.linear_eq_to_matrix(sysOfEq, x, y, _lambda)
        lagrange = tuple(sympy.linsolve((A,b), [x,y,_lambda]))[:2])
        if all(good>=0 for good in lagrange):
            bundleA.append(lagrange)
        '''
        
            

        






