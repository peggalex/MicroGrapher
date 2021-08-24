
var isOpen = true

function toggle(){
  if (isOpen){
    closeNav()
  } else {
    openNav()
  }
  isOpen = !isOpen
}

function openNav() {
  $("#mySidebar").addClass('open');
}

function closeNav() {
  $("#mySidebar").removeClass('open');
}

openNav()


var win = null;

function openDemandCurve(){
  win = window.open('./micrographer/demandCurve/','popUpWindow',
    'height=600,width=640,left=100,top=100,resizable=yes,'+
    'scrollbars=yes,toolbar=yes,menubar=no,location=no,'+
    'directories=no, status=yes')
  win.focus(); //if a window is already open, open will not focus nor open a new version.
  //this is the workaround, courtesy of stackoverflow
}

function openHelp(){
  win = window.open('./micrographer/help/','popUpWindow',
    'height=600,width=800,left=100,top=100,resizable=yes,'+
    'scrollbars=yes,toolbar=yes,menubar=no,location=no,'+
    'directories=no, status=yes')
  win.focus(); //if a window is already open, open will not focus nor open a new version.
  //this is the workaround, courtesy of stackoverflow
}


var width = 1,
    height = 1,
    px_1,
    px_2,
    py,
    m,
    disableAnimations,
    forceDecimal,
    calculator = null,
    bundleToColorsDic = null;
    interval = null,
    msg = null,
    allExpressions = null;

  const socket = io.connect('https://' + document.domain),

    bundleNames = ['a','b','c','d','e'],
    bundleNamesDic = {
      'a':'A',
      'c':'C',
      'b':'B<sub>hicksian</sub>',
      'd':'D<sub>slutsky</sub>',
      'e':'E<sub>ev</sub>'
    },
    plots = ['bl','curve','point']


  function CurveParams(suffix, subKey){
  	this.suffix = suffix
  	this.subKey = subKey
  }

DesmosExpressionPrototype = function(id, latex, color, label=null){
  this.id = id
  this.latex = latex
  this.color = color
  this.label = label
  this.showLabel = true

}

AdjustableSlider = function(c, subKey, endVal){
  this.c = c
  this.subKey = subKey
  this.endVal = parseFloat(endVal)

  this.adjustVal = function(subVal){
    calculator.setExpression({
      id: this.c+'_'+this.subKey+'-slider',
      latex: this.subKey+'='+subVal
    })
  }

  this.adjust = function(progressFrac, startVal=0){
    if (progressFrac==1){
    	this.adjustVal('\\infty')
    }
    var subVal = parseFloat(startVal) + (this.endVal-parseFloat(startVal))*progressFrac
    this.adjustVal(subVal)
  }

}

Bundle = function(c, hexColors){

  var latexAddBounds = (s) => s+'\\{x>0\\}\\{y>0\\}'
  var curves = [new CurveParams('curve','u'),new CurveParams('bl','m')]
  for (let i=0;i<curves.length;i++) {

    var o = curves[i],
        json_key = c+'_'+o.suffix,
        latexSub = (k) => k+'_\{'+c+'\}',
        //subtitute in a new name for the sub so we can create a desmos slider
        // that only affects that curve.
        trueFunc = msg[json_key]['func'],
        funcNewSub = trueFunc.replace(o.subKey, latexSub(o.subKey)),
        funcFormatted;

    this[o.subKey] = msg[json_key][o.subKey]

    if (o.subKey=='m'){
      funcFormatted = funcNewSub + '\\{'+latexSub('x')+'>x>=0\\}\\{y>=0\\}'
      var xInter;
      if (c=='a' || px_1<px_2) {
        xInter = (px_1.indexOf('x')==-1) ? m/eval(px_1) : m
      } else {
        xInter = (px_2.indexOf('x')==-1) ? m/eval(px_2) : m
      }
      this.bl_xBound = new AdjustableSlider(c, latexSub('x'), xInter)
    } else {
      funcFormatted = funcNewSub+'\\{x>0\\}\\{y>0\\}'

    }
    calculator.setExpression({
      id: json_key,
      latex: latexAddBounds(funcFormatted),
      color: bundleToColorsDic[c][o.suffix]
    })
    this[o.subKey+'_slider'] = new AdjustableSlider(
        c, latexSub(o.subKey), msg[json_key][o.subKey])

  }

  this.point = new DesmosExpressionPrototype(c+'_point',
    twoValsToTupStr(...msg[c]),bundleToColorsDic[c]['point'],
    'Bundle '+c)  

  this.plotPoint = () => calculator.setExpression(this.point)

  this.draw_bl = (progressFrac, startVal=0) => this.bl_xBound.adjust(progressFrac, startVal)

  this.move_bl = (progressFrac, startVal=0) => this.m_slider.adjust(progressFrac, startVal)

  this.move_curve = (progressFrac, startVal=0) => this.u_slider.adjust(progressFrac, startVal)

}

Bundles = function(){
  for (let i=0; i<bundleNames.length; i++){
    var c = bundleNames[i]
    this[c] = new Bundle(c)
  }
}

latexify = (s) => '\\('+s+'\\)'

twoValsToTupStr = (arg1,arg2) => '('+arg1+', '+arg2+')'

truncZeros = function(i, d=3){
  let floatCat = (parseFloat(i)+'')
  let toFixedCat = d==null ? i : parseFloat(i).toFixed(d)
  if (floatCat.length<toFixedCat.length){
    return floatCat
  } else if (floatCat.length==toFixedCat.length && d!=null){
    return floatCat
  } else {
    return toFixedCat+'...'
  }
}

cleanVal = function(deci, simp, d){
	let deciRet = latexify(truncZeros(deci,d))
  if (simp==null){
  	return deciRet
  } else {
  	let simpRet = latexify(simp),
  		id = 'simpleVal_'+simpRet+'_'+deciRet,
  		dic = {'s': simpRet, 'd': deciRet},
  		k
  	if ($('#isDecimal').prop("checked")){
  		k = 'd'
  	} else {
  		k = 's'
  	}
  	return '<a class="simpVal '+k+'" id="'+id+'">'+dic[k]+'</a>'
  }
}

tupToStr = function(lst, d=3){
  args = []
  lst.forEach(function(i){args.push(truncZeros(i,d))})
  return twoValsToTupStr(...args)
}

bundToStr = function(deci, simp, d=3){
  let bund = []	
  for (let i=0; i<2; i++){ bund.push(cleanVal(deci[i],simp[i],d)) }
  return twoValsToTupStr(...bund)

}

getColorFromInt = function(i){
  //precond: 255*6 > i >= 0
  i = i%(128*6)
  rgb = [127,127,127]
  index = Math.floor(i/(2*128))
  indexNext = (index==2) ? 0 : index+1
  
  if (Math.floor(i/128)%2==1){
      rgb[index] = 255-(i%128)
      rgb[indexNext] = 255
  } else {
      rgb[index] = 255
      rgb[indexNext] = 127+(i%128)
  }
      
  return rgb
}

rgbToHex = function(rgbLst){
  //better than the complicated solutions available online
  ret = '#'
  rgbLst.forEach((c)=>ret += c<16 ? '0'+c.toString(16) : c.toString(16))
  return ret
}

setColorDic = function() {
  let maxPercentDarken = 0.5,
      i = parseInt(Math.random()*(128*6)),
      percentDarken,
      brightest,
      colors,
      shade;

  bundleToColorsDic = {}

  for (let j=0; j<bundleNames.length; j++){
    percentDarken = 1-maxPercentDarken*j/(bundleNames.length-1)
    colors = {}
    for (let k=0; k<plots.length; k++){
      shade = []

      brightest = getColorFromInt(i+k*(128*6)/plots.length)
      brightest.forEach(function(c){
        shade.push(Math.ceil(c*percentDarken))
      })
      colors[plots[k]] = rgbToHex(shade)
    }
    bundleToColorsDic[bundleNames[j]] = colors
  }
}

loadingInfoDiv = function() {
  closeOpenTab()
  let idsToClear = ['tabButtons','functionLabel','bundleTable']
  idsToClear.forEach((id)=>document.getElementById(id).innerHTML='')

  $("#infoDiv").width("0");
  let s = '<div class=loaderContainer>'+'<div class="loader">'+'</div>'+'</div>'
  document.getElementById('calculator').innerHTML = s
  clearInterval(interval)
  if (calculator!=null) {calculator.destroy(); calculator=null;}

}

closeOpenTab = function(){
  let selected = document.querySelector(".tabActive")
  if (selected==null) {return}
  selected.className = 'tabContent'
  let tab = selected.id.slice(0,selected.id.indexOf('-'))
  let button = document.getElementById(tab+'-button')
  if (button==null) {return}
  document.getElementById(tab+'-button').className = 'tabButton'

}

openTabStr = function(str){
  if (calculator!==null){
    calculator.getExpressions().forEach(function(e){
      if (e.id!="LoV"){
        calculator.removeExpression(e)
      }
    })
    /*clear all curves first*/
    if (str=='home'){
      allExpressions.forEach(function(e){
        if (e.id!="LoV"){
          calculator.setExpression(e) 
        }
      })
    } else {
      addRelevantExpr = function(expr){
        if (expr.id[0]==str){
          calculator.setExpression(expr)
        }        
      }
      allExpressions.forEach(addRelevantExpr)
      if (str=='b' || str=='e'){
        let prefix = (str=='b') ? 'a' : 'c'
        calculator.setExpression(allExpressions.find((e)=>e.id==prefix+'_curve'))
        calculator.setExpression(allExpressions.find((e)=>e.id==prefix+'_point'))
        calculator.setExpression(allExpressions.find((e)=>e.id.slice(0,3)==prefix+'_u'))
      } else if (str=='d'){
        calculator.setExpression(allExpressions.find((e)=>e.id=='a_point'))                            
      }
    }
  }
  str+='-content'
  document.getElementById(str).className += ' tabActive'
}

selectTab = (str) => document.getElementById(str+'-button').className += ' selected'

openTab = function(evt){
  let buttonId = evt.currentTarget.id
  let prefix = buttonId.slice(0,buttonId.indexOf('-'))
  closeOpenTab()
  openTabStr(prefix)
  selectTab(prefix)
}

populateTabContent = function() {
  curves = [new CurveParams('curve','u'),new CurveParams('bl','m')];

  addFunctions = function(c){
    let str = '<h3> Bundle '
    str+= '<span style="color:'+bundleToColorsDic[c]['point']+' ">'+bundleNamesDic[c]+'</span>: '
    str+= bundToStr(msg[c],msg[c+'_simp'],5) + '</h3>' 
    addPlots = function(o){
      let dir = msg[c+'_'+o.suffix],
      	v = o.subKey,
      	finalVal = cleanVal(dir[v],dir[v+'_simp'],5),
      	spanTag = '<span style="color:'+bundleToColorsDic[c][o.suffix]+' "> ',
      	func = dir['func']

      func = func.replace('='+v,'')+'='+'\\)'+finalVal

      if (v=='u' && (c=='b' || c=='e')){
        oldF = (c=='b') ? 'a' : 'c'
        func+=' \\(=\\) <span style="color:'+bundleToColorsDic[oldF]['curve']+' ">'
        func+='\\(u_'+oldF+'(x,y)\\)' + '</span>'
      }

      func = spanTag+'\\('+v+'_{'+c+'}(x,y)\\)</span>\\(='+func
      str+='<h3 style="font-size:90%;">'+func+'</h3>'
    }
    curves.forEach(addPlots)

    if ((c=='b' || c=='d' || c=='e') && !checkPyY()){
      let cv_or_ev = (c=='e') ? 'equivalent variation' : 'compensating variation'
      str+= '<h3>' + cv_or_ev+': \\('+getV(msg,c,5)+'\\)' + '</h3>'
    }
    str+='<h3>tangency condition: \\('+msg[c+'_tan']+'\\)' + '</h3>'

    document.getElementById(c+'-content').innerHTML = str
  }
  bundleNames.forEach(addFunctions)
}

addSimpClickSwitch = function() {
	$('a.simpVal').on('click', function(){
    let split = this.id.split('_')
    	str1 = split[1]
    	str2 = split[2]
    if (this.className.split(' ')[1] == 's'){
    	this.innerHTML = str2
    	this.className = 'simpVal d'
    } else {
    	this.innerHTML = str1
    	this.className = 'simpVal s'
    }
    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
	})

}


handleFinish = function() {
  clearInterval(interval)

  populateTabContent()
  MathJax.Hub.Queue(["Typeset",MathJax.Hub]);

  $('a.simpVal').unbind('click')
  addSimpClickSwitch()

  document.getElementById('tabButtons').innerHTML = ''
  //get rid of line break in there
  addButton = function(c){
    document.getElementById('tabButtons').innerHTML += getButtonStr(c)
  }
  addButton('home')
  bundleNames.forEach(addButton)
  selectTab('home')

  allExpressions = calculator.getExpressions()
  //save expressions so we may remove/add then with buttons
}

getButtonStr = (s) => '<button id="'+s+
	'-button" class="tabButton" onclick="openTab(event)">'+
	s+'</button>'

getV = (msg,c,d) => truncZeros(Math.abs(parseFloat(msg[c+'_bl']['m'])-m)+'',d)

checkPyY = () => py.indexOf('y')>-1


toggleSimple = function(k,newK) {
  	let elems = Array.from(document.getElementsByClassName(k))
  	elems.forEach(function(e){
  		let split = e.id.split('_')
  		let index = k=='s' ? 2 : 1
  		e.innerHTML = split[index]
  		e.className = 'simpVal '+newK
  	})
  	MathJax.Hub.Queue(["Typeset",MathJax.Hub]);

  	//do this instead of $(a.k).trigger('click')
  	// because trigger will call MathJax
  	// n times for n buttons,
  	// whereas this only calls it once.
  	// there is noticable lag with repeated mathjax calls
}

setForceDecimalHandler = function(){
	$('#isDecimal').unbind('change')

$('#isDecimal').change(function() {
    if (this.checked) {
    	//$('a.s').trigger('click')
    	toggleSimple('s','d')
    } else {
    	//$('a.d').trigger('click')
    	toggleSimple('d','s')
    }
  })
}

setInfoDiv = function() {

  _getFuncLabelStr = function() {
    let str = '<h3>'
    str +='function: <span style="font-size:90%;">\\('+msg.a_curve.func+'\\)</span>'
    if (msg.funcType.length>0) {str+=', '+msg.funcType}
    str+='</h3>'
    if (msg.LoV.length>0) { 
      str+='<h3>line of vertices: <span style="font-size:90%">'
      str+='\\('+msg.LoV+'\\)' + '</span></h3>'
    }

    str+='<h3 style="font-size:90%;">'
    str+='\\(p_x:'+px_1+'\\rightarrow '+px_2+'\\)'
    str+='<span class=tabSpace>\\(p_y='+py+'\\)</span>'
    str+='<span class=tabSpace>\\(m='+m+'\\)</span>'
    str+='</h3>'

    if (!checkPyY()){
      str+='<h3 style="font-size:95%;">'
      str+='CV<sub>hicksian</sub>: \\('+getV(msg,'b',2)+'\\)'
      str+='<span class=tabSpace>CV<sub>slutsky</sub>: \\('+getV(msg,'d',2)+'\\)</span>'
      str+='<span class=tabSpace>EV: \\('+getV(msg,'e',2)+'\\)</span>'
      str+='</h3>'
    }
    return str+'<br>'
  }

  _getTableStr = function() {
    let str = '<table align="center"><span class="tableHeading">'
    let headings = ['Bundle','Point','Income','Utility']
    headings.forEach((h)=>str+='<th>'+h+'</th>')
    str+='</tr></span>'
    addRow = function(c){
      let name = bundleNamesDic[c]
      let point = bundToStr(msg[c],msg[c+'_simp'],2)
      let income = cleanVal(msg[c+'_bl']['m'],msg[c+'_bl']['m_simp'],2)
      let u = cleanVal(msg[c+'_curve']['u'],msg[c+'_curve']['u_simp'],2)
      let cols = [
      {val:name,colorKey:''},{val:point,colorKey:'point'},
      {val:income,colorKey:'bl'},{val:u,colorKey:'curve'}
      ]
      str += '<tr>'
      cols.forEach(function(col){
        let bod = col.val
            currColor = bundleToColorsDic[c][col.colorKey]
        if (col.colorKey.length>0){
          bod =  '<span style="color:'+currColor+'">'+bod+'</span>'
        }
        str+='<td align="center">'+bod+'</td>'
      })
      str+='</tr>'
    }
    bundleNames.forEach(addRow)
    return str+'</table>'
  }

	$("#infoDiv").width("auto");
  document.getElementById('tabButtons').innerHTML = '<br><br>'
  document.getElementById('functionLabel').innerHTML = _getFuncLabelStr()
  document.getElementById('bundleTable').innerHTML = _getTableStr()
  MathJax.Hub.Queue(["Typeset",MathJax.Hub]);

  openTabStr('home')
  addSimpClickSwitch()
  setForceDecimalHandler()
}

calcInit = function(){
	let calcElt = document.getElementById('calculator')

	calcElt.innerHTML = ''
  calculator = Desmos.GraphingCalculator(calcElt, {
    expressions:false, 
    settingsMenu:false, 
    zoomButtons:true
  })

  const resizeObserver = new ResizeObserver(entries => {
    if (calculator==null) return
    let aspectRatioScreen = $('#calculator').width()/$('#calculator').height(),
        padding = 0.2,
        rightBound = parseFloat(msg['axis_max_x']),
        topBound = parseFloat(msg['axis_max_y']),
        aspectRatioGraph = rightBound/topBound

	  if (aspectRatioScreen<aspectRatioGraph){
	    topBound = rightBound/aspectRatioScreen
	  } else {
	    rightBound = topBound*aspectRatioScreen
	  }

    calculator.setMathBounds({
      left: 0,
      right: rightBound*(1+padding),
      bottom: 0,
      top: topBound*(1+padding)
    })

    calculator.setDefaultState(calculator.getState())
  })

  resizeObserver.observe(document.getElementById('calculator'))
    
  calculator.updateSettings({fontSize: Desmos.FontSizes.SMALL});

  if (msg.LoV.length!=0){
    calculator.setExpression({
      id: 'LoV',
      latex: msg.LoV+'\\{x>0\\}\\{y>0\\}',
      lineStyle: Desmos.Styles.DASHED,
      color: '#808080'
    })
  }
}

socket.on('connect', function() {
	$('form').unbind('submit')
$('form').on('submit', handleSubmit)
})

handleSubmit = function(e) {
  e.preventDefault()
  closeNav()
  u = $('input.u').val()
  px_1 = $('input.px_1').val()
  px_2 = $('input.px_2').val()
  py = $('input.py').val()
  m = $('input.m').val()

  disableAnimations = !$('#enableAnimations').prop("checked")

  let inputs = [u,px_1,px_2,py,m],
    invalidChars = ['<','>','{','}',';']

  let someInvalidChars = inputs.some((input)=>{
    return invalidChars.some((char)=>(input.indexOf(char)>-1))
  })

  if (someInvalidChars){
    alert('Pathological input including characters "<", ">", "{", "}" or ";".')
    throw "bad input"
  }

  socket.emit('genGraphs', {
    u : u,
    px_1 : px_1,
    px_2 : px_2,
    py : py,
    m : m,
    width: width,
    height: height
  })
  loadingInfoDiv()
}


socket.on('displayGraphs', function(json) {
  loadingInfoDiv() //call this again incase another request goes through
  msg = json
  console.log(msg)
  if( typeof msg['a_curve'] == 'undefined' ) {
    let errorMsg = 'undefined error'
    if (msg.error == 1){
      errorMsg = 'Invalid input, click here for input formatting.'
    } else if (msg.error == -1){
      errorMsg = 'Could not solve (sorry). You may have chosen too complex a function. If you believe this is an error, please send a message in help.'
    }
    document.getElementById('calculator').innerHTML = ''
    alert(errorMsg)
    return
  }
  //else
  finishedDrawing = false
  setColorDic()
  setInfoDiv()
  calcInit()

  var bundles = new Bundles()

  estTime_ms = (disableAnimations) ? 1 : 2000
  startTime = null
  state = null

/*
  setAnimeFuncs = function(objs){
    isFirstTime = true
    animeFunc = function(timestamp){
      if (isFirstTime) {
        console.log('start:',performance.now(),'timestamp:',timestamp)
        startTime = timestamp
        isFirstTime = false
      }
      let progressFrac = (timestamp - startTime)/estTime_ms
      if (progressFrac <= 1){
        //  alert(progressFrac)
        objs.forEach((obj)=>obj.f(progressFrac, obj.start))
        window.requestAnimationFrame(animeFunc)
      } else {
        objs.forEach((obj)=>obj.f(1, obj.start))
        setNextAnime()
      }
    }
    window.requestAnimationFrame(animeFunc)
  }

  setAnimeFunc = function(animeFunc, startVal){
    setAnimeFuncs([{f:animeFunc, start:startVal}])
  }
*/

//this is the better way to code a solution to possibly
// multiple solutions. But forEach is slow,
// and especially in an event loop, unideal.
// below is a hardcoded solution

  setAnimeFuncs = function(func1, startVal1, func2, startVal2){
    startTime = performance.now()
    animeFunc = function(timestamp){
      let progressFrac = (timestamp - startTime)/estTime_ms
      if (progressFrac <= 1){
        func1(progressFrac, startVal1)
        func2(progressFrac, startVal2)
        window.requestAnimationFrame(animeFunc)
      } else {
        func1(1)
        func2(1)
        setNextAnime()
      }
    }
    window.requestAnimationFrame(animeFunc)
  }

  setAnimeFunc = function(func, startVal){
    startTime = performance.now()
    //these requestAnimationFrame examples
    // usually have a conditional statement
    // inside that says
    // `iff startTime == null: startTime = 0`
    // but this is an extra step every 
    // iteration of the event loop
    // so i think it's better to hardcode startTime outside

    animeFunc = function(timestamp){
      let progressFrac = (timestamp - startTime)/estTime_ms
      if (progressFrac <= 1){
        func(progressFrac, startVal)
        window.requestAnimationFrame(animeFunc)
      } else {
        func(1)
        setNextAnime()
      }
    }
    window.requestAnimationFrame(animeFunc)
  }

  setNextAnime = function(){
    state = (state==null) ? 0 : state + 1
    //could just initialize state as -1 and +=1
    // but that's unreadable imo

    switch(state){
      case 0:
        bundles.a.move_bl(0,bundles.a.m)
        setAnimeFunc(bundles.a.draw_bl)
        break

      case 1:
        setAnimeFunc(bundles.a.move_curve)
        break

      case 2:
        bundles.a.plotPoint()
        setNextAnime()
        break

      case 3:
        bundles.c.move_bl(0,bundles.c.m)
        setAnimeFunc(bundles.c.draw_bl)
        break

      case 4:
        setAnimeFunc(bundles.c.move_curve, bundles.a.u)
        break

      case 5:
        bundles.c.plotPoint()
        bundles.b.draw_bl(1)
        setNextAnime()
        break

      case 6:
        setAnimeFunc(bundles.b.move_bl, bundles.c.m)
        break

      case 7:
        bundles.b.plotPoint()
        bundles.d.draw_bl(1)
        setNextAnime()
        break

      case 8:
        setAnimeFuncs(
          bundles.d.move_curve,
          bundles.c.u,
          bundles.d.move_bl,
          bundles.c.m)
        break

      case 9:
        bundles.d.plotPoint()
        bundles.e.draw_bl(1)
        setNextAnime()
        break

      case 10:
        setAnimeFunc(bundles.e.move_bl, bundles.a.m)
        break
      case 11:
        bundles.e.plotPoint()
        setNextAnime()
        break

      case 12:
        handleFinish()
        break
    }
  }

  setNextAnime()
/*
  totalTime_ms = 0

  skipACase = () => totalTime_ms+=estTime_ms-1

  intervalFunc = function() {
    //let state = Math.floor(totalTime_ms/estTime_ms),
    let state = Math.floor(totalTime_ms/estTime_ms),
        stateTime = (totalTime_ms%estTime_ms)+1,
        progressFrac = stateTime/estTime_ms

    switch(state){
      case 0:
        bundles.a.move_bl(0,bundles.a.m)
        bundles.a.draw_bl(progressFrac)
        break

      case 1:
        bundles.a.move_curve(progressFrac)
        break

      case 2:
        bundles.a.plotPoint()
        skipACase()
        break

      case 3:
        bundles.c.move_bl(0,bundles.c.m)
        bundles.c.draw_bl(progressFrac)
        break

      case 4:
        bundles.c.move_curve(progressFrac, bundles.a.u)
        break

      case 5:
        bundles.c.plotPoint()
        bundles.b.draw_bl(1)
        skipACase()
        break

      case 6:
        bundles.b.move_bl(progressFrac, bundles.c.m)
        break

      case 7:
        bundles.b.plotPoint()
        bundles.d.draw_bl(1)
        skipACase()
        break

      case 8:
        bundles.d.move_curve(progressFrac, bundles.c.u)
        bundles.d.move_bl(progressFrac, bundles.c.m)
        break

      case 9:
        bundles.d.plotPoint()
        bundles.e.draw_bl(1)
        skipACase()
        break

      case 10:
        bundles.e.move_bl(progressFrac, bundles.a.m)
        //setAnime(bundles.e.move_bl, bundles.a.m)
        break
      case 11:
        bundles.e.plotPoint()
        skipACase()
        break

      case 12:
        handleFinish()
        break
    }
    totalTime_ms+=1
  }

  interval = setInterval(intervalFunc,1)

*/

})
