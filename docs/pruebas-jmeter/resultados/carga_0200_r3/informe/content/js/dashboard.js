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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.8218895471857808, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9292709466811752, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.8102477477477478, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9325, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9365, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.881198347107438, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9291799787007454, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9104972375690608, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9512338425381903, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.014874141876430207, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9859223300970874, 500, 1500, "GET /health"], "isController": false}, {"data": [0.7796127562642369, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8578, 0, 0.0, 361.61517836325623, 3, 962, 367.0, 568.0, 634.0, 801.0, 96.25764461650677, 487.73732720712, 36.359893553975205], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 919, 0, 0.0, 363.7029379760615, 9, 855, 371.0, 533.0, 593.0, 731.9999999999995, 11.214565511855223, 1.8508413784214186, 4.3587862048031045], "isController": false}, {"data": ["GET /findings", 888, 0, 0.0, 457.8806306306304, 14, 956, 466.5, 625.1, 668.0, 789.4300000000002, 11.247055247359222, 254.5195422334524, 4.514198932289688], "isController": false}, {"data": ["POST /auth/login", 200, 0, 0.0, 218.30000000000007, 53, 826, 100.0, 539.8, 573.6999999999999, 813.9000000000001, 9.575792396820836, 20.516883318969647, 2.281731782054965], "isController": false}, {"data": ["GET /auth/me", 1000, 0, 0.0, 318.74899999999974, 6, 854, 323.5, 523.8, 585.8499999999998, 778.9200000000001, 11.560159067788772, 19.07877814898733, 4.233456689864052], "isController": false}, {"data": ["GET /dashboard/summary", 968, 0, 0.0, 399.2004132231404, 13, 918, 406.0, 596.3000000000001, 663.55, 857.2399999999998, 11.399232200475753, 6.545652865116936, 4.285844137874184], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 939, 0, 0.0, 354.4653887113952, 10, 859, 365.0, 528.0, 584.0, 783.0000000000002, 11.264395393474087, 1.8590652553682823, 4.356152906070058], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 905, 0, 0.0, 388.4143646408836, 10, 882, 394.0, 552.0, 596.6999999999999, 802.6399999999996, 11.222022444044887, 3.5616770452290907, 4.361684504619009], "isController": false}, {"data": ["GET /alerts/unread-count", 851, 0, 0.0, 342.6768507638075, 9, 839, 334.0, 497.0, 552.9999999999999, 752.9200000000001, 11.267493743959115, 1.980614134680313, 4.258320389562673], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 874, 0, 0.0, 3236.438215102977, 426, 4810, 3278.0, 3834.5, 4010.5, 4267.5, 11.252156448747328, 544.6556129222777, 38.5234255309048], "isController": true}, {"data": ["GET /health", 1030, 0, 0.0, 204.41553398058235, 3, 682, 196.0, 376.9, 451.44999999999993, 614.8999999999994, 11.708936305660076, 2.5384608006411495, 4.276506033512567], "isController": false}, {"data": ["GET /logs", 878, 0, 0.0, 484.8917995444194, 28, 962, 484.0, 662.3000000000001, 717.0999999999999, 916.21, 11.37836296718677, 256.1798420004795, 4.355779573376186], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8578, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
