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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.837830396475771, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9378531073446328, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.8452941176470589, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9552631578947368, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9572916666666667, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.8858520900321544, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9268426842684269, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.938150289017341, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.951397326852977, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.02874251497005988, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9919354838709677, 500, 1500, "GET /health"], "isController": false}, {"data": [0.8198090692124105, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8245, 0, 0.0, 334.57719830200085, 2, 892, 347.0, 552.0, 618.0, 741.0, 92.63732683167983, 466.95317459453616, 34.9946947013022], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 885, 0, 0.0, 341.7480225988701, 10, 802, 357.0, 527.0, 587.3999999999999, 712.28, 10.779405853765484, 1.7790230364124675, 4.189651884569007], "isController": false}, {"data": ["GET /findings", 850, 0, 0.0, 428.20941176470626, 13, 878, 440.0, 620.6999999999999, 690.7999999999997, 780.47, 10.791458243404513, 244.20943542423126, 4.33133724417896], "isController": false}, {"data": ["POST /auth/login", 190, 0, 0.0, 193.02631578947367, 57, 745, 94.0, 474.0, 641.0, 733.1700000000001, 8.937391222541041, 19.149058927983443, 2.1296127522461075], "isController": false}, {"data": ["GET /auth/me", 960, 0, 0.0, 289.71041666666673, 7, 760, 310.0, 481.69999999999993, 554.0, 668.0, 11.140380397572326, 18.38597936708714, 4.079729149501584], "isController": false}, {"data": ["GET /dashboard/summary", 933, 0, 0.0, 375.56806002143617, 12, 861, 404.0, 599.0, 662.5999999999999, 772.6199999999998, 10.963701101070518, 6.295562741630336, 4.1220946522579585], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 909, 0, 0.0, 342.8107810781073, 10, 793, 364.0, 547.0, 607.5, 709.4999999999999, 10.855805288174459, 1.791631927442855, 4.198143451286216], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 865, 0, 0.0, 349.8404624277457, 9, 792, 357.0, 526.0, 584.6999999999999, 720.7200000000003, 10.743206319240896, 3.409709036868448, 4.175582143611208], "isController": false}, {"data": ["GET /alerts/unread-count", 823, 0, 0.0, 321.17375455650057, 8, 773, 320.0, 499.20000000000005, 570.5999999999999, 668.52, 10.833936681366419, 1.9044029322714406, 4.094466304383597], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 835, 0, 0.0, 3101.6682634730505, 175, 4568, 3129.0, 3859.0, 4044.3999999999996, 4360.68, 10.65921160130719, 515.9767624599482, 36.54150869332108], "isController": true}, {"data": ["GET /health", 992, 0, 0.0, 174.99596774193552, 2, 597, 168.0, 322.0, 416.3499999999999, 534.1399999999999, 11.295189296897238, 2.4487617421007686, 4.125391403358952], "isController": false}, {"data": ["GET /logs", 838, 0, 0.0, 447.2708830548928, 20, 892, 453.5, 635.1, 690.3499999999997, 826.44, 10.800082482730177, 243.16006019467213, 4.1344065754201464], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8245, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
