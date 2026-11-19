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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [1.0, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [1.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [1.0, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [1.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [1.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [1.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 529, 0, 0.0, 12.425330812854442, 3, 110, 10.0, 21.0, 23.0, 70.70000000000005, 6.018887245420412, 30.46191661807373, 2.2780495327966777], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 58, 0, 0.0, 9.482758620689658, 7, 23, 9.0, 11.100000000000001, 13.0, 23.0, 0.7358445084431814, 0.12144308781923599, 0.2860020648050646], "isController": false}, {"data": ["GET /findings", 55, 0, 0.0, 12.981818181818184, 8, 23, 12.0, 17.0, 20.199999999999996, 23.0, 0.7162111129920696, 16.20777355602073, 0.2874636400778717], "isController": false}, {"data": ["POST /auth/login", 10, 0, 0.0, 73.50000000000001, 64, 110, 70.5, 106.70000000000002, 110.0, 110.0, 0.5766680122253619, 1.2355562683812928, 0.1374091747880745], "isController": false}, {"data": ["GET /auth/me", 61, 0, 0.0, 8.098360655737707, 6, 14, 8.0, 11.0, 11.0, 14.0, 0.7239926413862678, 1.1948706679128835, 0.2651340239451665], "isController": false}, {"data": ["GET /dashboard/summary", 60, 0, 0.0, 14.533333333333335, 10, 23, 14.0, 18.9, 22.0, 23.0, 0.7264714072961945, 0.4171535034083617, 0.27313622246976066], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 58, 0, 0.0, 11.896551724137934, 8, 21, 11.0, 16.0, 16.099999999999994, 21.0, 0.7361527136112098, 0.12149395371122507, 0.28468405721683504], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 58, 0, 0.0, 9.72413793103448, 7, 24, 9.0, 12.100000000000001, 14.149999999999991, 24.0, 0.735629851352037, 0.23347627118106642, 0.2859186336309675], "isController": false}, {"data": ["GET /alerts/unread-count", 53, 0, 0.0, 8.943396226415095, 7, 14, 9.0, 11.0, 12.0, 14.0, 0.7114189452207412, 0.12505411146458342, 0.26886633964885437], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 54, 0, 0.0, 102.18518518518518, 85, 123, 102.5, 115.5, 120.25, 123.0, 0.7243460764587525, 35.06264147384306, 2.4820406815895373], "isController": true}, {"data": ["GET /health", 62, 0, 0.0, 5.032258064516129, 3, 30, 4.0, 8.700000000000003, 11.849999999999994, 30.0, 0.7317447391093959, 0.1586399727366073, 0.2672583324481583], "isController": false}, {"data": ["GET /logs", 54, 0, 0.0, 21.62962962962963, 18, 33, 21.0, 24.0, 31.25, 33.0, 0.7202112619701778, 16.21530336398677, 0.27570587372295874], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 529, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
