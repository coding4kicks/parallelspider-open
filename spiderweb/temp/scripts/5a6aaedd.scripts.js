function isEmpty(a){for(var b in a)if(a.hasOwnProperty(b))return!1;return!0}function LoginController(a,b,c,d){a.error={},a.error.show=!1,a.error.message="",a.close=function(e,f){if(f==="login")if(typeof e!="undefined"&&typeof e.user!="undefined"&&e.user!==""&&typeof e.password!="undefined"&&e.password!==""){var g=d.getProtocol()+"://"+d.getHost()+"/checkusercredentials",h={};h.user=e.user,h.password=e.password,b.post(g,h).success(function(b,d,e,f){b.login==="success"?c.close(b):(a.error.show=!0,a.error.message="Invalid Email and Password.")}).error(function(b,c,d,e){a.error.show=!0,a.error.message="Server Error."})}else a.error.show=!0,a.error.message="Must enter both email and password.";else c.close("cancelled")}}"use strict";var spiderwebApp=angular.module("spiderwebApp",["ngCookies"]).config(["$routeProvider","$locationProvider",function(a,b){a.when("/",{templateUrl:"views/main.html",controller:"MainCtrl"}).when("/ourwords",{templateUrl:"views/ourwords.html",controller:"OurwordsCtrl"}).when("/ourwords/:pageName",{templateUrl:"views/ourwords.html",controller:"OurwordsCtrl"}).when("/launchpad",{templateUrl:"views/launchpad.html",controller:"LaunchpadCtrl"}).when("/spiderdiaries",{templateUrl:"views/spiderdiaries.html",controller:"SpiderdiariesCtrl"}).when("/spiderdiaries/:pageType/:pageName",{templateUrl:"views/spiderdiaries.html",controller:"SpiderdiariesCtrl"}).when("/splashdown",{templateUrl:"views/splashdown.html",controller:"SplashdownCtrl"}).when("/splashdown/:analysisId",{templateUrl:"views/splashdown.html",controller:"SplashdownCtrl"}).when("/myaccount/accountId",{templateUrl:"views/myaccount.html",controller:"MyaccountCtrl"}).when("/signup",{templateUrl:"views/signup.html",controller:"SignupCtrl"}).when("/crawling",{templateUrl:"views/crawling.html",controller:"CrawlingCtrl"}).otherwise({redirectTo:"/"})}]).service("sessionService",function(){var a="",b="",c="";return{setShortSession:function(a){b=a},getShortSession:function(){return b},setLongSession:function(b){a=b},getLongSession:function(b){return a},setUserName:function(a){c=a},getUserName:function(){return c}}}).run(["$cookieStore","sessionService",function(a,b){b.setLongSession(a.get("ps_longsession")),b.setShortSession(a.get("ps_shortsession")),b.setUserName(a.get("ps_username"))}]);Array.prototype.remove=function(a,b){var c=this.slice((b||a)+1||this.length);return this.length=a<0?this.length+a:a,this.push.apply(this,c)},spiderwebApp.service("configService",function(){var a="localhost:8000",b="http",c=!0,d="new analyses";return{getHost:function(){return a},getProtocol:function(){return b},getMock:function(){return c},getDefaultFolder:function(){return d}}}).service("resultsService",["$http","$q","sessionService","configService",function(a,b,c,d){var e={};return{getCurrentAnalysis:function(){return e},setCurrentAnalysis:function(a){e={id:a}},getAnalysis:function(f){e={id:f};var g=d.getProtocol()+"://"+d.getHost()+"/gets3signature",h={analysisId:f,shortSession:c.getShortSession(),longSession:c.getLongSession()},i=b.defer();return typeof h.shortSession=="undefined"&&(h.shortSession=""),typeof h.longSession=="undefined"&&(h.longSession=""),a.post(g,h).success(function(b,c,d,e){b.url!=="error"?a.get(b.url).success(function(a,b,c,d){i.resolve(a)}).error(function(a,b,c,d){console.log("error")}):console.log("error")}).error(function(a,b,c,d){console.log("error")}),i.promise}}}]).service("folderService",["$http","$q","sessionService","configService",function(a,b,c,d){var e={},f=function(){var e=d.getProtocol()+"://"+d.getHost()+"/getanalysisfolders",f={shortSession:c.getShortSession(),longSession:c.getLongSession()},g=b.defer();return typeof f.shortSession=="undefined"&&(f.shortSession=""),typeof f.longSession=="undefined"&&(f.longSession=""),a.post(e,f).success(function(a,b,c,d){g.resolve(a)}).error(function(a,b,c,d){console.log("error")}),g.promise},g=function(e){var f=d.getProtocol()+"://"+d.getHost()+"/updateanalysisfolders",g={folderInfo:e,shortSession:c.getShortSession(),longSession:c.getLongSession()},h=b.defer();return typeof g.shortSession=="undefined"&&(g.shortSession=""),typeof g.longSession=="undefined"&&(g.longSession=""),a.post(f,g).success(function(a,b,c,d){h.resolve(a)}).error(function(a,b,c,d){console.log("error")}),h.promise};return{addAnalysis:function(a,c,d,h){var i=b.defer();if(isEmpty(e))f().then(function(b){e=b;var f={};for(var j=0;j<e.length;j++)e[j].name===a?f=e[j]:f=e[0];analysis={name:c,date:d,id:h},f.analysisList.push(analysis),g(e),i.resolve("done")});else{var j={};for(var k=0;k<e.length;k++)e[k].name===a?j=e[k]:j=e[0];analysis={name:c,date:d,id:h},j.analysisList.push(analysis),i.resolve("done")}return i.promise},addFolder:function(){},getFolderList:function(){var a=b.defer();return isEmpty(e)?f():(a.resolve(e),a.promise)}}}]).service("crawlService",["$http","$q","sessionService","configService","resultsService","folderService",function(a,b,c,d,e,f){var g="",h="",i="",j=0;return{getCrawlId:function(){return g},setCrawlId:function(a){g=a},getCrawlName:function(){return h},setCrawlName:function(a){h=a},getCrawlDate:function(){return i},setCrawlDate:function(a){i=a},getMaxPages:function(){return j},setMaxPages:function(a){j=a},getCrawlStatus:function(){var e=d.getProtocol()+"://"+d.getHost()+"/checkcrawlstatus",f={id:g,shortSession:c.getShortSession(),longSession:c.getLongSession()},h=b.defer();return typeof f.shortSession=="undefined"&&(f.shortSession=""),typeof f.longSession=="undefined"&&(f.longSession=""),a.post(e,f).success(function(a,b,c,d){h.resolve(a)}).error(function(a,b,c,d){console.log("error")}),h.promise},initiateCrawl:function(e){var f=d.getProtocol()+"://"+d.getHost()+"/initiatecrawl",k={},l=b.defer();return now=(new Date).toString(),k.shortSession=c.getShortSession(),k.longSession=c.getLongSession(),typeof k.shortSession=="undefined"&&(k.shortSession=""),typeof k.longSession=="undefined"&&(k.longSession=""),e.time=now,typeof e.maxPages=="undefined"&&(e.maxPages=20),k.crawl=e,a.post(f,k).success(function(a,b,c,d){g=a.crawlId,j=e.maxPages,i=e.time,h=e.name,l.resolve(a)}).error(function(a,b,c,d){console.log("error")}),l.promise}}}]),spiderwebApp.directive("psFullscreen",function(){return function(a,b,c){var d=window.innerHeight-190;a.minHeight=d+"px"}}).directive("integer",function(){var a=/^\-?\d*$/;return{require:"ngModel",link:function(b,c,d,e){e.$parsers.unshift(function(b){return a.test(b)?(e.$setValidity("integer",!0),b):(e.$setValidity("integer",!1),undefined)})}}}).directive("tooltipPopup",function(){return{restrict:"E",replace:!0,scope:{tooltipTitle:"@",placement:"@",animation:"&",isOpen:"&"},templateUrl:"views/tooltip/tooltip-popup.html"}}).directive("tooltip",["$compile","$timeout","$parse",function(a,b,c){var d='<tooltip-popup tooltip-title="{{tt_tooltip}}" placement="{{tt_placement}}" animation="tt_animation()" is-open="tt_isOpen"></tooltip-popup>';return{scope:!0,link:function(e,f,g){function j(){return{width:f.prop("offsetWidth"),height:f.prop("offsetHeight"),top:f.prop("offsetTop"),left:f.prop("offsetLeft")}}function k(){var a,c,d,g;i&&b.cancel(i),h.css({top:0,left:0,display:"block"}),f.after(h),a=j(),c=h.prop("offsetWidth"),d=h.prop("offsetHeight");switch(e.tt_placement){case"right":g={top:a.top+a.height/2-d/2+"px",left:a.left+a.width+"px"};break;case"bottom":g={top:a.top+a.height+"px",left:a.left+a.width/2-c/2+"px"};break;case"left":g={top:a.top+a.height/2-d/2+"px",left:a.left-c+"px"};break;default:g={top:a.top-d+"px",left:a.left+a.width/2-c/2+"px"}}h.css(g),e.tt_isOpen=!0}function l(){e.tt_isOpen=!1,angular.isDefined(e.tt_animation)&&e.tt_animation()?i=b(function(){h.remove()},500):h.remove()}var h=a(d)(e),i;g.$observe("tooltip",function(a){e.tt_tooltip=a}),g.$observe("tooltipPlacement",function(a){e.tt_placement=a||"top"}),g.$observe("tooltipAnimation",function(a){e.tt_animation=c(a)}),e.tt_isOpen=!1,f.bind("mouseenter",function(){e.$apply(k)}),f.bind("mouseleave",function(){e.$apply(l)})}}}]).controller("TabsController",["$scope","$element",function(a,b){var c=a.panes=[];this.select=a.select=function(b){angular.forEach(c,function(a){a.selected=!1}),b.selected=!0},this.addPane=function(d){c.length||a.select(d),c.push(d)},this.removePane=function(d){var e=c.indexOf(d);c.splice(e,1),d.selected&&c.length>0&&a.select(c[e<c.length?e:e-1])}}]).directive("tabs",function(){return{restrict:"EA",transclude:!0,scope:{},controller:"TabsController",templateUrl:"views/tabs/tabs.html",replace:!0}}).directive("pane",["$parse",function(a){return{require:"^tabs",restrict:"EA",transclude:!0,scope:{heading:"@"},link:function(b,c,d,e){var f,g;b.selected=!1,d.active&&(f=a(d.active),g=f.assign,b.$watch(function(){return f(b.$parent)},function(c){b.selected=c}),b.selected=f?f(b.$parent):!1),b.$watch("selected",function(a){a&&e.select(b),g&&g(b.$parent,a)}),e.addPane(b),b.$on("$destroy",function(){e.removePane(b)})},templateUrl:"views/tabs/pane.html",replace:!0}}]).factory("$transition",["$q","$timeout","$rootScope",function(a,b,c){function h(a){for(var b in a)if(e.style[b]!==undefined)return a[b]}var d=function(e,f,g){g=g||{};var h=a.defer(),i=d[g.animation?"animationEndEventName":"transitionEndEventName"],j=function(a){c.$apply(function(){e.unbind(i,j),h.resolve(e)})};return i&&e.bind(i,j),b(function(){angular.isString(f)?e.addClass(f):angular.isFunction(f)?f(e):angular.isObject(f)&&e.css(f),i||h.resolve(e)}),h.promise.cancel=function(){i&&e.unbind(i,j),h.reject("Transition cancelled")},h.promise},e=document.createElement("trans"),f={WebkitTransition:"webkitTransitionEnd",MozTransition:"transitionend",OTransition:"oTransitionEnd",msTransition:"MSTransitionEnd",transition:"transitionend"},g={WebkitTransition:"webkitAnimationEnd",MozTransition:"animationend",OTransition:"oAnimationEnd",msTransition:"MSAnimationEnd",transition:"animationend"};return d.transitionEndEventName=h(f),d.animationEndEventName=h(g),d}]).controller("MessageBoxController",["$scope","dialog","model",function(a,b,c){a.title=c.title,a.message=c.message,a.buttons=c.buttons,a.close=function(a){b.close(a)}}]).provider("$dialog",function(){var a={backdrop:!0,dialogClass:"modal",backdropClass:"modal-backdrop",transitionClass:"fade",triggerClass:"in",dialogOpenClass:"modal-open",resolve:{},backdropFade:!1,dialogFade:!1,keyboard:!0,backdropClick:!0},b={},c={value:0};this.options=function(a){b=a},this.$get=["$http","$document","$compile","$rootScope","$controller","$templateCache","$q","$transition","$injector",function(d,e,f,g,h,i,j,k,l){function n(a){var b=angular.element("<div>");return b.addClass(a),b}function o(c){var d=this,e=this.options=angular.extend({},a,b,c);this.backdropEl=n(e.backdropClass),e.backdropFade&&(this.backdropEl.addClass(e.transitionClass),this.backdropEl.removeClass(e.triggerClass)),this.modalEl=n(e.dialogClass),e.dialogFade&&(this.modalEl.addClass(e.transitionClass),this.modalEl.removeClass(e.triggerClass)),this.handledEscapeKey=function(a){a.which===27&&(d.close(),a.preventDefault(),d.$scope.$apply())},this.handleBackDropClick=function(a){d.close(),a.preventDefault(),d.$scope.$apply()}}var m=e.find("body");return o.prototype.isOpen=function(){return this._open},o.prototype.open=function(a,b){var c=this,d=this.options;a&&(d.templateUrl=a),b&&(d.controller=b);if(!d.template&&!d.templateUrl)throw new Error("Dialog.open expected template or templateUrl, neither found. Use options or open method to specify them.");return this._loadResolves().then(function(a){var b=a.$scope=c.$scope=a.$scope?a.$scope:g.$new();c.modalEl.html(a.$template);if(c.options.controller){var d=h(c.options.controller,a);c.modalEl.contents().data("ngControllerController",d)}f(c.modalEl)(b),c._addElementsToDom(),m.addClass(c.options.dialogOpenClass),setTimeout(function(){c.options.dialogFade&&c.modalEl.addClass(c.options.triggerClass),c.options.backdropFade&&c.backdropEl.addClass(c.options.triggerClass)}),c._bindEvents()}),this.deferred=j.defer(),this.deferred.promise},o.prototype.close=function(a){function e(a){a.removeClass(b.options.triggerClass)}function f(){b._open&&b._onCloseComplete(a)}var b=this,c=this._getFadingElements();m.removeClass(b.options.dialogOpenClass);if(c.length>0){for(var d=c.length-1;d>=0;d--)k(c[d],e).then(f);return}this._onCloseComplete(a)},o.prototype._getFadingElements=function(){var a=[];return this.options.dialogFade&&a.push(this.modalEl),this.options.backdropFade&&a.push(this.backdropEl),a},o.prototype._bindEvents=function(){this.options.keyboard&&m.bind("keydown",this.handledEscapeKey),this.options.backdrop&&this.options.backdropClick&&this.backdropEl.bind("click",this.handleBackDropClick)},o.prototype._unbindEvents=function(){this.options.keyboard&&m.unbind("keydown",this.handledEscapeKey),this.options.backdrop&&this.options.backdropClick&&this.backdropEl.unbind("click",this.handleBackDropClick)},o.prototype._onCloseComplete=function(a){this._removeElementsFromDom(),this._unbindEvents(),this.deferred.resolve(a)},o.prototype._addElementsToDom=function(){m.append(this.modalEl),this.options.backdrop&&(c.value===0&&m.append(this.backdropEl),c.value++),this._open=!0},o.prototype._removeElementsFromDom=function(){this.modalEl.remove(),this.options.backdrop&&(c.value--,c.value===0&&this.backdropEl.remove()),this._open=!1},o.prototype._loadResolves=function(){var a=[],b=[],c,e=this;return this.options.template?c=j.when(this.options.template):this.options.templateUrl&&(c=d.get(this.options.templateUrl,{cache:i}).then(function(a){return a.data})),angular.forEach(this.options.resolve||[],function(c,d){b.push(d),a.push(angular.isString(c)?l.get(c):l.invoke(c))}),b.push("$template"),a.push(c),j.all(a).then(function(a){var c={};return angular.forEach(a,function(a,d){c[b[d]]=a}),c.dialog=e,c})},{dialog:function(a){return new o(a)},messageBox:function(a,b,c){return new o({templateUrl:"template/dialog/message.html",controller:"MessageBoxController",resolve:{model:function(){return{title:a,message:b,buttons:c}}}})}}}]}),"use strict",spiderwebApp.controller("MainCtrl",["$scope","$http","$timeout","$location","sessionService","crawlService","configService",function(a,b,c,d,e,f,g){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],a.spider1Margin="0px",a.spider2Margin="0px",a.spider3Margin="0px",a.text1Margin="-150px",a.text2Margin="-150px",a.text3Margin="-150px",a.move=function(b){var d="text"+b.slice(6,13),e;if(a[b]==="0px"||a[b]==="-0px"){var f=function(e,g){e+=5,a[b]="-"+e+"px",g-=5,a[d]=-1*g+"px",e<175&&c(function(){f(e,g)},10)};f(0,150)}else{var g=function(e,f){e-=5,a[b]="-"+e+"px",f-=5,a[d]=f+"px",e>0&&c(function(){g(e,f)},10)};g(170,20)}},a.for1MarginLeft="0px",a.for1MarginTop="0px",a.for2MarginLeft="0px",a.for2MarginTop="0px",a.for3MarginLeft="0px",a.for3MarginTop="0px",a.text1MarginTop="-50px",a.text1Visibility="hidden",a.text2MarginTop="-50px",a.text2Visibility="hidden",a.text3MarginTop="-50px",a.text3Visibility="hidden",a.animate=function(b){var d=b+"Left",e=b+"Top",f="text"+b.slice(3,13)+"Top",g,h=f.slice(0,5)+"Visibility";if(a[d]==="0px"||a[d]==="-0px"){var i=function(b,g){b+=5,a[d]=-1*b+"px",a[e]=-1*b+"px",g-=5,a[f]=-1*g+"px",b<35&&c(function(){i(b,g)},10)};i(0,50),a[h]="visible"}else{var j=function(b,g){b-=5,a[d]=-1*b+"px",a[e]=-1*b+"px",g-=5,a[f]=g+"px",b>0&&c(function(){j(b,g)},10)};j(35,-15),a[h]="hidden"}},a.showAdvOpts=!1,a.spanSize="span8",a.advOptMargin="-30px",a.showOptions=function(){a.spanSize==="span12"?a.spanSize="span8":a.spanSize="span12",a.showAdvOpts=!a.showAdvOpts},a.crawl={},a.crawl.name="",a.crawlName="",a.crawl.additionalSites=[],a.additionalSites,a.crawl.wordSearches=[],a.wordSearches,a.crawl.wordContexts=[],a.wordContexts,a.predefinedSynRings=[{name:"none",title:"None"},{name:"curseWords",title:"Curse Words"},{name:"racistLang",title:"Racist Language"},{name:"drugRefs",title:"Drug References"}],a.crawl.wordnets=[],a.wordnets,a.crawl.customSynRings=[],a.customSynRings,a.crawl.xpathSelectors=[],a.xpathSelectors,a.crawl.cssSelectors=[],a.cssSelectors,a.add=function(b){var c=a[b];if(typeof c!="undefined"&&c!="")if(c instanceof Object){var d={};for(var e in c)d[e]=c[e];a.crawl[b].push(d)}else a.crawl[b].push(c)},a.remove=function(b,c){a.crawl[b].remove(c)},a.attemptedSubmission=!1,a.crawlSite=function(){var b=e.getShortSession();typeof b=="undefined"&&(b=""),a.crawl.name=a.crawlName||a.crawl.primarySite,typeof a.crawl.maxPages!="undefined"&&a.crawl.maxPages>20?a.name!==""&&b!==""?f.initiateCrawl(a.crawl).then(function(b){b.loggedIn?(d.path("/crawling"),a.apply):a.openLogin()}):(alert("Must sign in to initiate crawl greater than 20 pages."),a.openLogin()):f.initiateCrawl(a.crawl).then(function(b){b.loggedIn?(d.path("/crawling"),a.apply):(alert("Free Crawl of 20 pages is currently disabled to avoid potential use in DDOS attacks.  Once caching is implemented, this feature will be enabled. Please log-in to try the system."),a.openLogin())})}}]),"use strict",spiderwebApp.controller("OurwordsCtrl",["$scope","$routeParams",function(a,b){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],a.aboutPages=["about","devteam","terms","contact"],typeof b["pageName"]=="undefined"?a.template="views/ourwords/about.html":a.template="views/ourwords/"+b.pageName+".html"}]),"use strict",spiderwebApp.controller("LaunchpadCtrl",function(a){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"]}),"use strict",spiderwebApp.controller("SpiderdiariesCtrl",["$scope","$routeParams",function(a,b){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],a.tutorials=["tutorial1"],a.examples=["testexample"],a.pageType={examples:!0,tutorials:!1},a.showLinks=function(b){for(var c in a.pageType)c===b?a.pageType[c]=!0:a.pageType[c]=!1};if(typeof b["pageType"]=="undefined")a.template="views/spiderdiaries/tutorials/tutorial1.html";else{var c=b.pageType;for(var d in a.pageType)d===b.pageType?a.pageType[d]=!0:a.pageType[d]=!1;if(typeof b["pageName"]=="undefined"){var e=a[c][0];a.template="views/spiderdiaries/"+c+"/"+e+".html"}else a.template="views/spiderdiaries/"+b.pageType+"/"+b.pageName+".html"}}]),"use strict",spiderwebApp.controller("SplashdownCtrl",["$scope","$http","resultsService","configService","sessionService","folderService",function(a,b,c,d,e,f){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],a.folderList=[],a.currentFolder={},a.results="internalResults",a.internal=!0,a.external=!1,a.summary={totalPages:0,totalWords:0,numberOfSites:0,minutes:0,seconds:0},a.commonGround=!0,a.commonWords={},a.commonColors=[],a.limitTo={text:50,links:50,context:50,synonyms:50,selectors:50},a.soloResults=!1,a.buttonTypes={};var g=[{type:"pages",active:!0,label:"Pages",itemType:"page"},{type:"tags",active:!1,label:"Tags",itemType:"tag"}];a.buttonTypes.visibleText=g,a.buttonTypes.headlineText=g,a.buttonTypes.hiddenText=g,a.buttonTypes.searchWords=g,a.buttonTypes.context=g,a.buttonTypes.synonymRings=g,a.buttonTypes.selectors=g,a.buttonTypes.allLinks=[{type:"pages",active:!0,label:"Pages",itemType:"page"},{type:"words",active:!1,label:"Words",itemType:"words"}],a.buttonTypes.externalDomains=[{type:"pages",active:!0,label:"Pages",itemType:"page"},{type:"words",active:!1,label:"Words",itemType:"words"},{type:"links",active:!1,label:"Links",itemType:"link"}],a.buttonTypes.linkText=[{type:"pages",active:!0,label:"Pages",itemType:"page"}],a.selectFolder=function(b){c.setCurrentAnalysis(""),a.analysisAvailable=!1;for(var d=0;d<a.folderList.length;d++)b===a.folderList[d].name&&(a.currentFolder=a.folderList[d])},a.selectAnalysis=function(b){c.setCurrentAnalysis(b),a.analysisAvailable=!0,a.getAnalysis(b)},a.getFoldlersOrAnalysis=function(b){isEmpty(b)?(a.analysisAvailable=!1,f.getFolderList().then(function(b){a.folderList=b,a.currentFolder=a.folderList[0]})):(a.analysisAvailable=!0,a.getAnalysis(b.id),f.getFolderList().then(function(b){a.folderList=b,a.currentFolder=a.folderList[0]}))},a.getAnalysis=function(b){c.getAnalysis(b).then(function(b){a.analysis=b,a.summary.minutes=Math.floor(a.analysis.time/60),a.summary.seconds=a.analysis.time%60,a.analysis.sites.length<2?a.commonGround=!1:a.commonGround=!0;for(var c=0;c<a.analysis.sites.length;c++)a.summary.totalPages=a.summary.totalPages+a.analysis.sites[c].internalResults.summary.pages.count,a.summary.totalPages=a.summary.totalPages+a.analysis.sites[c].externalResults.summary.pages.count,a.summary.totalWords=a.summary.totalWords+a.analysis.sites[c].internalResults.summary.words.count,a.summary.totalWords=a.summary.totalWords+a.analysis.sites[c].externalResults.summary.words.count,a.summary.numberOfSites=a.summary.numberOfSites+1,a.analysis.sites[c].include=!0,a.analysis.sites[c].additionalInfo={},a.analysis.sites[c].additionalInfo.text={showing:!1,buttonTypes:[],currentButton:{},currentItem:{},currentType:"",currentLabel:""},a.analysis.sites[c].additionalInfo.links={showing:!1,buttonTypes:[],currentButton:{},currentItem:{},currentType:"",currentLabel:""},a.analysis.sites[c].additionalInfo.context={showing:!1,buttonTypes:[],currentButton:{},currentItem:{},currentType:"",currentLabel:""},a.analysis.sites[c].additionalInfo.synonyms={showing:!1,buttonTypes:[],currentButton:{},currentItem:{},currentType:"",currentLabel:""},a.analysis.sites[c].additionalInfo.selectors={showing:!1,buttonTypes:[],currentButton:{},currentItem:{},currentType:"",currentLabel:""};a.show={text:!1,links:!1,context:!1,synonymRings:!1,selectors:!1,internalButton:!0,externalButton:!1},isEmpty(a.analysis.sites[0].internalResults)&&(a.results="externalResults",a.external=!0,a.show.internalButton=!1),isEmpty(a.analysis.sites[0].externalResults)||(a.show.externalButton=!0);if(isEmpty(a.analysis.sites[0].internalResults)||isEmpty(a.analysis.sites[0].externalResults))a.soloResults=!0;var d=["visibleText","hiddenText","headlineText","searchWords"];for(var c=0;c<d.length;c++)isEmpty(a.analysis.sites[0][a.results][d[c]])||(a.show.text=!0);var e=["allLinks","externalDomains","linkText"];for(var c=0;c<e.length;c++)isEmpty(a.analysis.sites[0][a.results][e[c]])||(a.show.links=!0);var f=["context","synonymRings","selectors"];for(var c=0;c<f.length;c++)if(!isEmpty(a.analysis.sites[0].internalResults[f[c]])||!isEmpty(a.analysis.sites[0].externalResults[f[c]]))a.show[f[c]]=!0;a.compareSites()})},a.compareSites=function(){var b=function(b,c){var d=[],e={},f={},g=[],h=c+"s",i=a.analysis.sites;for(var j=0;j<i.length;j++)i[j].include===!0&&b!=="context"&&b!=="synonymRings"&&b!=="selectors"&&d.push({site:j+1,items:i[j][a.results][b][h]}),i[j].include===!0&&b==="context"&&d.push({site:j+1,items:i[j][a.results].context.contextWords[c].words}),i[j].include===!0&&b==="synonymRings"&&d.push({site:j+1,items:i[j][a.results].synonymRings.rings[c].words}),i[j].include===!0&&b==="selectors"&&d.push({site:j+1,items:i[j][a.results].selectors[c].words});if(b==="context"||b==="synonymRings"||b==="selectors")c="word",h="words";if(d.length>0){g=d[0].items;for(var j=0;j<g.length;j++)e[g[j][c]]=[g[j].rank];for(var j=1;j<d.length;j++){f={},g=d[j].items;for(var k=0;k<g.length;k++)typeof e[g[k][c]]!="undefined"&&(f[g[k][c]]=e[g[k][c]],f[g[k][c]].push(g[k].rank));e=f}var l=[],m=e;for(var n in m)m.hasOwnProperty(n)&&l.push({word:n,rank:m[n]});return l}};isEmpty(a.analysis.sites[0][a.results].visibleText)||(a.commonWords.visibleText=b("visibleText","word")),isEmpty(a.analysis.sites[0][a.results].headlineText)||(a.commonWords.headlineText=b("headlineText","word")),isEmpty(a.analysis.sites[0][a.results].hiddenText)||(a.commonWords.hiddenText=b("hiddenText","word")),isEmpty(a.analysis.sites[0][a.results].allLinks)||(a.commonWords.allLinks=b("allLinks","link")),isEmpty(a.analysis.sites[0][a.results].externalDomains)||(a.commonWords.externalDomains=b("externalDomains","domain")),isEmpty(a.analysis.sites[0][a.results].linkText)||(a.commonWords.linkText=b("linkText","word"));var c=a.analysis.sites[0][a.results].context.contextWords||[];for(var d=0;d<c.length;d++)a.commonWords[c[d].word]=b("context",d);var e=a.analysis.sites[0][a.results].synonymRings.rings||[];for(var d=0;d<e.length;d++)a.commonWords[e[d].net]=b("synonymRings",d);var f=a.analysis.sites[0][a.results].selectors||[];for(var d=0;d<f.length;d++)a.commonWords[f[d].name]=b("selectors",d);a.commonColors=[];var g=a.analysis.sites;for(var d=0;d<g.length;d++)g[d].include===!0&&a.commonColors.push((d+1)%5)},a.resultsChoice=function(b){b==="internal"&&(a.results="internalResults",a.internal=!0,a.external=!1),b==="external"&&(a.results="externalResults",a.external=!0,a.internal=!1);for(var c=0;c<a.analysis.sites.length;c++){var d=a.analysis.sites[c].additionalInfo;d.text.showing=!1,d.text.currentItem={},d.links.showing=!1,d.links.currentItem={}}a.compareSites()},a.showInfo=function(b,c,d,e,f,g){var h=b.additionalInfo[c];h.currentItem===d?(h.showing=!1,h.currentItem={}):(h.showing=!0,h.currentItem=d,h.currentType=e,h.currentLabel=f,h.buttonTypes=a.buttonTypes[g],h.currentButton.active=!1,h.currentButton=a.buttonTypes[g][0],h.currentButton.active=!0)},a.switchInfoType=function(a,b){a.currentButton.active=!1,b.active=!0,a.currentButton=b};var h=c.getCurrentAnalysis();a.getFoldlersOrAnalysis(h)}]),"use strict",spiderwebApp.controller("MyaccountCtrl",function(a){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"]}),"use strict",spiderwebApp.controller("SignupCtrl",function(a){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"]}),"use strict",spiderwebApp.controller("TemplateCtrl",["$scope","$dialog","$cookieStore","$http","sessionService","configService",function(a,b,c,d,e,f){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],angular.element(window).bind("resize",function(){var b=window.innerHeight-190;a.minHeight=b+"px",a.$digest()}),a.name=e.getUserName(),a.opts={backdrop:!0,keyboard:!1,backdropClick:!1,templateUrl:"views/login.html",controller:"LoginController"},a.openLogin=function(){var d=b.dialog(a.opts);d.open().then(function(b){b&&b.login==="success"&&(a.name=b.name,e.setUserName(b.name),e.setShortSession(b.short_session),e.setLongSession(b.long_session),c.put("ps_longsession",b.long_session),c.put("ps_shortsession",b.short_session),c.put("ps_username",b.name))})},a.signout=function(){var b=f.getProtocol()+"://"+f.getHost()+"/signout",g={shortSession:e.getShortSession(),longSession:e.getLongSession()};d.post(b,g).success(function(b,d,f,g){console.log("logged out"),c.remove("ps_longsession"),c.remove("ps_shortsession"),c.remove("ps_username"),e.setShortSession(""),e.setLongSession(""),a.name=""}).error(function(a,b,c,d){console.log("error")})},a.openMessageBox=function(){var a="This is a message box",c="This is the content of the message box",d=[{result:"cancel",label:"Cancel"},{result:"ok",label:"OK",cssClass:"btn-primary"}];b.messageBox(a,c,d).open().then(function(a){alert("dialog closed with result: "+a)})}}]),"use strict",spiderwebApp.controller("CrawlingCtrl",["$scope","$timeout","$http","$q","$location","configService","resultsService","crawlService","folderService",function(a,b,c,d,e,f,g,h,i){a.awesomeThings=["HTML5 Boilerplate","AngularJS","Testacular"],a.maxPages=h.getMaxPages();var j={};j.id=h.getCrawlId(),j.name=h.getCrawlName(),j.date=h.getCrawlDate();var k=a.maxPages/20;a.pagesCrawled=0,a.pageCount={},a.pageCount.count=-1,a.status={},a.status.initializing=!0,a.status.crawling=!1;var l=0;a.progress=l+"%";var m=!0,n=0;a.quoteList=[{words:"a",author:"b"}],a.quote={},a.time={},a.time.minutes=Math.floor(k/60),a.time.seconds=k%60,c.get("quote-file.json").then(function(b){a.quoteList=b.data,a.quote=a.quoteList[Math.floor(Math.random()*a.quoteList.length)]});var o=function(c){h.getCrawlStatus().then(function(b){a.pageCount=b}),a.pageCount.count===-1?b(function(){o()},500):(a.status.initializing=!1,a.status.crawling=!0,m(c))},m=function(c){a.pageCount.count===-2&&(f.getMock()===!0?(g.setCurrentAnalysis("results1SiteSearchOnly"),i.addAnalysis(f.getDefaultFolder(),j.name,j.date,j.id).then(function(b){a.status.crawling=!1,e.path("/splashdown").replace()})):(g.setCurrentAnalysis(crawlId),i.addAnalysis(f.getDefaultFolder(),j.name,j.date,j.id).then(function(b){a.status.crawling=!1,e.path("/splashdown").replace()}))),a.pageCount.count-a.pagesCrawled>100&&(a.pagesCrawled=a.pageCount.count),a.pagesCrawled<a.maxPages&&a.pagesCrawled-a.pageCount.count<100&&(n%20===0&&(k-=1,a.time.minutes=Math.floor(k/60),a.time.seconds=k%60),a.pagesCrawled+=1,c=a.pagesCrawled/a.maxPages*100,a.progress=c+"%",n%300===0&&(a.quote=a.quoteList[Math.floor(Math.random()*a.quoteList.length)])),n%100===0&&h.getCrawlStatus().then(function(b){a.pageCount=b}),n+=1,a.status.crawling&&b(function(){m(c)},50)};o(l)}]);