spiderwebApp.service('configService', function() {
    // change4deployment
    var host = 'localhost:8000',
        protocol = 'http';

    return {
      setHost: function (configHost) {
        host = configHost;
      },
      getHost: function () {
        return host;
      },
      setProtocol: function (configProtocol) {
        protocol = configProtocol;
      },
      getProtocol: function () {
        return protocol;
      }
    };
  })

  .service('resultsService', function ($http, $q, sessionService, configService) {

    // Where am I setting this???
    // Either get the results passed, the current if one is set, or none
    var currentAnalysis = {};
    //var currentAnalysis = {'id': 'results1SiteSearchOnly'};
    
    return {
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


        $http.post(url, data)
          .success(function(data, status, headers, config){
            console.log(data.url);
            if (data.url !== 'error') {
              $http.get(data.url)
                .success(function(data, status, headers, config){
                  deferred.resolve(data);
                })
                .error(function(data, status, headers, config){
                  console.log('error');
                });
            }
            else {
              console.log('error');
            }
          })
          .error(function(data, status, headers, config){
            console.log("error");
          });

        return deferred.promise;
        // Must later account for user ???
        //return currentAnalysis;
      },

      getCurrentAnalysis: function () {
        return currentAnalysis;
      },

      setCurrentAnalysis: function (analysisId) {
        currentAnalysis = {'id': analysisId};
      },

      listAnalyses:function () {
        // This function will take the "user"??? and list their analyses
        // later funcionality should also allow them to place analysis into folders like gmail
        // even later timeseries analysis should be enabled.
      }
    };
  })

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

