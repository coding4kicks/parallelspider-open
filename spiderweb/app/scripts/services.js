  /*
   * Config Service - provides one place for host and protocol configuration
   *
   * Used as an easy to find location for anything that will change upon deployment
   * TODO: once larger, refactor to read from a file
   *
   */
spiderwebApp.service('configService', function() {

    // change4deployment
    var host = 'localhost:8000',
        protocol = 'http',
        mock = false;

    // TODO: later allow user to set
    var defaultFolder = "new analyses";

    return {

      getHost: function () {
        return host;
      },

      getProtocol: function () {
        return protocol;
      },

      getMock: function () {
        return mock;
      },

      getDefaultFolder: function () {
        return defaultFolder;
      }

    };
  })


  /*
   * Results Service - retrieves the results of a crawl from S3
   *
   * Functions:
   *  getAnalysis - fetches the requested analysis from the server
   *  getCurrentAnalysis - Getter for the current analysis id
   *  setCurrentAnalysis - Setter for the current analysis id
   *
   */
  .service('resultsService', ['$http', '$q', 'sessionService', 'configService', function ($http, $q, sessionService, configService) {

    // Holds id of current analysis if one exists.
    // Initialized at the end of a crawl so splashdown shows results
    // Set on analysis selection so analysis reapears on page refresh
    var currentAnalysis = {};

    return {

      getCurrentAnalysis: function () {
        return currentAnalysis;
      },

      setCurrentAnalysis: function (analysisId) {
        currentAnalysis = {'id': analysisId};
      },

     /*
      * Get Analysis - fetches the requested analysis from the server
      *
      * args:
      *  analysisId - the id of the analysis to retrieve from S3
      */
      getAnalysis:function (analysisId) {

        // set currentAnalysis
        currentAnalysis = {'id':analysisId};

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/gets3signature',
            data = {'analysisId': analysisId,
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();

        // QA data - since "" returned from session service will trigger undefined
        if (typeof data.shortSession === "undefined") {
          data.shortSession = "";
        }
        if (typeof data.longSession === "undefined") {
          data.longSession = "";
        }

        // First fetch is to retrieve signed URL from the server
        $http.post(url, data)

          .success(function(data, status, headers, config){
            
            // If able to sign URL without an error from the server
            if (data.url !== 'error') {

              // Second fetch is to retrieve analysis from S3
              $http.get(data.url)

                .success(function(data, status, headers, config){
                  deferred.resolve(data);
                })

                .error(function(data, status, headers, config){
                  console.log('error');
                });
            }

            // Request reached server but server wouldn't sign (shouldn't happen)
            else {
              console.log('error');
            }
          })

          .error(function(data, status, headers, config){
            console.log("error");
          });

        return deferred.promise;
      }
    };
  }])


  /*
   * Folder Service - Used to maintain user's analyses folders
   *
   * Functions:
   *  getFolderList - Getter for folder list from local or server
   *    FolderList = [folderInfo1, ...]
   *      FolderInfo =
   *        {'name': 'foldername', 'analysisList': [analysisInfo1, ...]}
   *      AnslysisInfo = 
   *        {'name': 'analysisname', 'date': 'date', 'id': 'id'} 
   *  addAnalysis - add an analysis to a folder
   *  addFolder - add a folder to the list
   */
  .service('folderService', ['$http', '$q', 'sessionService', 'configService', function ($http, $q, sessionService, configService) {
    
    var folderList = {};

    var fetchFolderList = function() {

      // Configure resource fetch details
      var url = configService.getProtocol() + '://' + 
                configService.getHost() + '/getanalysisfolders',
          data = {'shortSession': sessionService.getShortSession(),
                  'longSession': sessionService.getLongSession() },
          deferred = $q.defer();

      // QA data - since "" returned from session service will trigger undefined
      if (typeof data.shortSession === "undefined") {
        data.shortSession = "";
      }
      if (typeof data.longSession === "undefined") {
        data.longSession = "";
      }

      $http.post(url, data)
        .success(function(data, status, headers, config){
          deferred.resolve(data);
        })
        .error(function(data, status, headers, config){
          console.log('error');
        });

      return deferred.promise;

    };

    var updateFolderList = function(folders) {
      // Don't need folder argument, could just manipulate folderList

      // Configure resource fetch details
      var url = configService.getProtocol() + '://' + 
                configService.getHost() + '/updateanalysisfolders',
          data = {'folderInfo': folders,
                  'shortSession': sessionService.getShortSession(),
                  'longSession': sessionService.getLongSession() },
          deferred = $q.defer();

      // QA data - since "" returned from session service will trigger undefined
      if (typeof data.shortSession === "undefined") {
        data.shortSession = "";
      }
      if (typeof data.longSession === "undefined") {
        data.longSession = "";
      }

      $http.post(url, data)
        .success(function(data, status, headers, config){
          deferred.resolve(data);
        })
        .error(function(data, status, headers, config){
          console.log('error');
        });

      return deferred.promise;

    };  

    // Public functions  
    return {

      addAnalysis:function (folderName, analysisName, date, id) {

        var deferred = $q.defer();

        if (isEmpty(folderList)) {
          fetchFolderList()
            .then( function(results) {

              folderList = results;
              var folder = {};

              for (var i = 0; i < folderList.length; i++) {
                
                // Add to default folder
                if (folderList[i]['name'] === folderName) {
                  folder = folderList[i];
                }
                // Add to first if default not availabe
                else {
                  folder = folderList[0];
                }
              }

              analysis = {'name': analysisName, 'date': date, 'id': id};
              folder['analysisList'].push(analysis);

              // Update folders on server
              updateFolderList(folderList);

              deferred.resolve('done');
            });
        }

        else {

          var folder = {};

          for (var i = 0; i < folderList.length; i++) {            
            // Add to default folder
            if (folderList[i]['name'] === folderName) {
              folder = folderList[i];
            }
            // Add to first if default not availabe
            else {
              folder = folderList[0];
            }
          }

          analysis = {'name': analysisName, 'date': date, 'id': id};
          folder['analysisList'].push(analysis);

          deferred.resolve('done');
        }

        return deferred.promise
      },

      addFolder:function () {
        //TODO: later
      },

      /*
       * Get Folder List - fetches folder list from server
       *
       * Returns: deferred object
       *    FolderList = [folderInfo1, ...]
       *      FolderInfo =
       *        {'name': 'foldername', 'analysisList': [analysisInfo1, ...]}
       *      AnslysisInfo = 
       *        {'name': 'analysisname', 'date': 'date', 'id': 'id'}        
       *   
       */
      getFolderList:function () {

        var deferred = $q.defer(); 

        // If empty fetch from server
        if (isEmpty(folderList)) {

          return fetchFolderList();
        }

        // Otherwise return from local
        else {

          deferred.resolve(folderList);
        }

        return deferred.promise
      }
    };
  }])

  /*
   * Crawl Service - Used to initiate and monitor a crawl
   *
   * Functions:
   *  getCrawlId - Unique Crawl ID getter
   *  setCrwalId - Unique Crawl ID setter
   *  getMaxPages - Max Pages to crawl getter
   *  setMaxPages - Max Pages to crawl setter
   *  getCrawlStatus - fetches crawl status from server
   *  initiateCrawl - send crawl data to the server
   */
  .service('crawlService', ['$http', '$q', 'sessionService', 'configService', 'resultsService', 'folderService', function ($http, $q, sessionService, configService, resultsService, folderService) {

    var crawlId = "",
        crawlName = "",
        crawlDate = "",
        maxPages = 0;
    
    return {

      getCrawlId:function () {
        return crawlId;
      },

      setCrawlId:function (id) {
        crawlId = id;
      },

      getCrawlName:function () {
        return crawlName;
      },

      setCrawlName:function (name) {
        crawlName = name;
      },

      getCrawlDate:function () {
        return crawlDate;
      },

      setCrawlDate:function (date) {
        crawlDate = date;
      },

      getMaxPages:function () {
        return maxPages;
      },

      setMaxPages:function (pages) {
        maxPages = pages;
      },

      /*
       * Get Crawl Status - fetches crawl status from server
       *
       * Returns: deferred object
       *  - contains info about the status of the crawl
       *  - either int for number of pages
       *  - -1 for initiating
       *  - or -2 for complete
       * 
       */
      getCrawlStatus:function () {

        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/checkcrawlstatus',
            data = {'id': crawlId, 
                    'shortSession': sessionService.getShortSession(),
                    'longSession': sessionService.getLongSession() },
            deferred = $q.defer();

        // QA data - since "" returned from session service will trigger undefined
        if (typeof data.shortSession === "undefined") {
          data.shortSession = "";
        }
        if (typeof data.longSession === "undefined") {
          data.longSession = "";
        }

        $http.post(url, data)
          .success(function(data, status, headers, config){
            deferred.resolve(data);
          })
          .error(function(data, status, headers, config){
            console.log('error');
          });

        return deferred.promise;
      },

      /*
       * Initiates a Crawl - sends crawl data to server
       *
       * Returns: deferred object
       *  - crawl id
       */
      initiateCrawl:function (crawl) {
        
        // Configure resource fetch details
        var url = configService.getProtocol() + '://' + 
                  configService.getHost() + '/initiatecrawl',
            requestData = {},
            deferred = $q.defer();
            now = new Date().toString();

        // Construct request with session info
        requestData.shortSession = sessionService.getShortSession();
        requestData.longSession = sessionService.getLongSession();

        // QA data - since "" returned from session service will trigger undefined
        if (typeof requestData.shortSession === "undefined") {
          requestData.shortSession = "";
        }
        if (typeof requestData.longSession === "undefined") {
          requestData.longSession = "";
        }

        // Set the time
        crawl.time = now;

        // QA max pages
        if (typeof crawl.maxPages === "undefined") {
          crawl.maxPages = 20;
        }

        // Set crawl data in response
        requestData.crawl = crawl; 

        $http.post(url, requestData)

          .success(function(data, status, headers, config){

            // Set crawl info and return success
            crawlId = data.crawlId;
            maxPages = crawl.maxPages;
            crawlDate = crawl.time;
            crawlName = crawl.name;
            
            deferred.resolve(data);
          })

          .error(function(data, status, headers, config){
            console.log('error');
          });

        return deferred.promise;
      }
    };
  }]);



