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
        protocol = 'http';

    return {
      //setHost: function (configHost) {
      //  host = configHost;
      //},
      getHost: function () {
        return host;
      },
      //setProtocol: function (configProtocol) {
      //  protocol = configProtocol;
      //},
      getProtocol: function () {
        return protocol;
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
  .service('resultsService', function ($http, $q, sessionService, configService) {

    // Holds id of current analysis if one exists.
    // Initialized at the end of a crawl so splashdown shows results
    // Set on analysis selection so analysis reapears on page refresh
    var currentAnalysis = {};

    return {

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
      },

      getCurrentAnalysis: function () {
        return currentAnalysis;
      },

      setCurrentAnalysis: function (analysisId) {
        currentAnalysis = {'id': analysisId};
      }
    };
  })

  /*
   * Crawl Service - Used to initiate a crawl
   *
   * Functions:
   *  getCrawlId - Unique Crawl ID getter
   *  setCrwalId - Unique Crawl ID setter
   *  getMaxPages - Max Pages to crawl getter
   *  setMaxPages - Max Pages to crawl setter
   *  getCrawlStatus - fetches crawl status from server
   */
  .service('crawlService', function ($http, $q, sessionService, configService) {
    var crawlId = "",
        maxPages = 0;
    
    return {

      getCrawlId:function () {
        return crawlId;
      },

      setCrawlId:function (id) {
        crawlId = id;
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


        $http.post(url, data)
          .success(function(data, status, headers, config){
            deferred.resolve(data);
          })
          .error(function(data, status, headers, config){
            console.log('error');
          });

        return deferred.promise;
      }
    };
  });

