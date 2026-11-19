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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9361188586140313, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9973175965665236, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.9858437146092865, 500, 1500, "GET /findings"], "isController": false}, {"data": [1.0, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9989743589743589, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9942648592283628, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9973572938689218, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9994541484716157, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9987937273823885, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.36013986013986016, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [0.975609756097561, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8464, 0, 0.0, 147.62275519848677, 2, 682, 109.0, 336.0, 396.75, 508.7000000000007, 95.12891406478296, 481.74343768966213, 35.98334379987412], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 932, 0, 0.0, 141.88412017167397, 7, 565, 114.5, 317.70000000000005, 353.3499999999999, 448.3399999999999, 11.426329598116862, 1.8857907246892087, 4.441092949268077], "isController": false}, {"data": ["GET /findings", 883, 0, 0.0, 187.9082672706682, 9, 682, 160.0, 399.80000000000007, 468.5999999999999, 583.16, 11.240245936071897, 254.36544831698637, 4.511465898169482], "isController": false}, {"data": ["POST /auth/login", 175, 0, 0.0, 143.08, 53, 463, 84.0, 351.0, 383.0, 453.8800000000001, 8.55829420970266, 18.336813961023083, 2.039281042155712], "isController": false}, {"data": ["GET /auth/me", 975, 0, 0.0, 118.99589743589749, 5, 530, 77.0, 287.4, 335.0, 424.1600000000001, 11.313923668728316, 18.672393554834816, 4.143282593528435], "isController": false}, {"data": ["GET /dashboard/summary", 959, 0, 0.0, 169.20333680917622, 10, 612, 134.0, 370.0, 426.0, 529.1999999999995, 11.360405610310842, 6.523357909045679, 4.2712462499703845], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 946, 0, 0.0, 152.91331923890067, 7, 582, 130.0, 330.0, 378.0, 454.5899999999999, 11.407486011962185, 1.8826807968961028, 4.411488731188501], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 916, 0, 0.0, 147.69432314410483, 7, 548, 123.0, 316.60000000000014, 364.15, 421.4900000000001, 11.481142599300604, 3.643917328879586, 4.462397221212539], "isController": false}, {"data": ["GET /alerts/unread-count", 829, 0, 0.0, 147.88661037394434, 6, 518, 132.0, 308.0, 352.5, 440.0, 10.96778461334921, 1.9279308890652909, 4.145051411490376], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 858, 0, 0.0, 1354.0652680652697, 182, 2676, 1341.5, 1785.4, 1948.7999999999993, 2201.23, 11.050862302134183, 534.8975221290941, 37.80300970572893], "isController": true}, {"data": ["GET /health", 988, 0, 0.0, 66.5455465587044, 2, 403, 38.0, 161.10000000000002, 198.54999999999995, 300.44000000000005, 11.25618064574931, 2.4403047884339326, 4.111144103037346], "isController": false}, {"data": ["GET /logs", 861, 0, 0.0, 208.71660859465737, 21, 680, 161.0, 444.0, 499.79999999999995, 604.14, 11.11111111111111, 250.16276041666669, 4.253472222222222], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8464, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
