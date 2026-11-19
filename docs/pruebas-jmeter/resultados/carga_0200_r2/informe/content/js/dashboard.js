/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.7519793270288102, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.8312917594654788, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.7226066897347174, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9325, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.8742171189979123, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.774331550802139, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.8183807439824945, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.8325714285714285, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.873125, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.015024038461538462, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.963477366255144, 500, 1500, "GET /health"], "isController": false}, {"data": [0.7040332147093713, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8262, 0, 0.0, 432.305374001453, 2, 1270, 423.5, 697.0, 811.8499999999995, 1012.0, 92.74600929480702, 472.3126300592432, 35.03118966233358], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 898, 0, 0.0, 446.01781737193784, 10, 1104, 421.0, 686.3000000000001, 868.2499999999998, 985.0699999999999, 11.005306567643418, 1.8163054784489627, 4.277453138595782], "isController": false}, {"data": ["GET /findings", 867, 0, 0.0, 543.6136101499422, 13, 1239, 519.0, 777.0, 939.9999999999995, 1089.0399999999986, 10.984694911818366, 248.58235858551467, 4.408896102302098], "isController": false}, {"data": ["POST /auth/login", 200, 0, 0.0, 219.64999999999995, 51, 760, 96.5, 555.4000000000001, 635.9, 748.9200000000001, 9.655305590421936, 20.687246548228252, 2.300678285217727], "isController": false}, {"data": ["GET /auth/me", 958, 0, 0.0, 377.88204592901894, 6, 1065, 370.5, 631.3000000000001, 691.6499999999994, 927.0, 11.093740953042673, 18.30900606508019, 4.0626492747959], "isController": false}, {"data": ["GET /dashboard/summary", 935, 0, 0.0, 477.5647058823526, 12, 1149, 478.0, 715.0, 835.7999999999994, 1001.28, 11.006992677701128, 6.320421576648695, 4.138371270424741], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 914, 0, 0.0, 444.95404814004416, 10, 1128, 427.5, 695.5, 877.0, 982.5500000000001, 11.004888385869435, 1.8162364621210296, 4.255796680472945], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 875, 0, 0.0, 450.66628571428555, 10, 1125, 418.0, 705.3999999999999, 859.1999999999996, 987.24, 10.931077991679889, 3.4693362766562146, 4.248602578797457], "isController": false}, {"data": ["GET /alerts/unread-count", 800, 0, 0.0, 415.9762500000005, 93, 1032, 384.0, 624.9, 766.0999999999988, 951.6800000000003, 10.494005299472677, 1.8446493690479315, 3.9659961434530526], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 832, 0, 0.0, 3952.7151442307722, 409, 5548, 4069.5, 4857.8, 5043.499999999999, 5260.819999999998, 10.783487784330244, 521.9468926187544, 36.86937009915106], "isController": true}, {"data": ["GET /health", 972, 0, 0.0, 249.14814814814804, 2, 829, 231.0, 470.0, 523.0499999999997, 733.1599999999999, 11.067715746444552, 2.3994461872174715, 4.042310243330335], "isController": false}, {"data": ["GET /logs", 843, 0, 0.0, 559.2313167259796, 37, 1270, 532.0, 776.2, 913.3999999999999, 1095.4799999999968, 10.872649418319705, 244.793879237657, 4.162186105450512], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8262, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
