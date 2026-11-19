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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.6544085552160629, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.7117067833698031, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.5758980301274623, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9119047619047619, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.78125, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.6624338624338625, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.7048387096774194, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.6985458612975392, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.7574626865671642, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.013922518159806295, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9401015228426396, 500, 1500, "GET /health"], "isController": false}, {"data": [0.5468187274909964, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8338, 0, 0.0, 506.0157112017276, 3, 1074, 525.5, 722.0, 787.0, 922.0, 93.59915583395075, 469.2776257058104, 35.33980630205878], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 914, 0, 0.0, 511.1586433260392, 10, 948, 524.0, 681.5, 748.0, 907.8000000000006, 11.129511470459304, 1.8368041391676002, 4.325728091057425], "isController": false}, {"data": ["GET /findings", 863, 0, 0.0, 621.1622247972184, 15, 1074, 629.0, 777.6, 830.5999999999999, 960.72, 10.903072569233878, 246.73525453794596, 4.376135572221801], "isController": false}, {"data": ["POST /auth/login", 210, 0, 0.0, 252.64285714285717, 55, 1009, 102.0, 685.8, 837.9, 1003.6999999999996, 9.898656610888523, 21.208645121376385, 2.3586642705632808], "isController": false}, {"data": ["GET /auth/me", 960, 0, 0.0, 457.90625000000034, 7, 935, 483.0, 652.0, 754.249999999999, 873.56, 11.132887244726374, 18.37361273787849, 4.076985074973038], "isController": false}, {"data": ["GET /dashboard/summary", 945, 0, 0.0, 546.0105820105821, 13, 1046, 574.0, 754.0, 845.7999999999997, 978.6199999999999, 11.143473697864462, 6.398791537445609, 4.189684935232244], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 930, 0, 0.0, 512.6860215053761, 10, 1012, 528.5, 703.9, 783.3499999999998, 903.3799999999999, 11.106466829879977, 1.8330008732907386, 4.295078969367648], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 894, 0, 0.0, 525.5816554809845, 9, 1013, 531.0, 691.5, 779.0, 912.0, 11.145464519024584, 3.5373788756669824, 4.331928592355259], "isController": false}, {"data": ["GET /alerts/unread-count", 804, 0, 0.0, 501.15671641791056, 146, 928, 497.0, 644.0, 691.5, 854.95, 10.529762294545217, 1.8509347783380263, 3.9795097734267566], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 826, 0, 0.0, 4663.312348668282, 296, 6006, 4815.5, 5536.3, 5632.65, 5830.76, 10.62625430967941, 514.3585040186152, 36.37927731661349], "isController": true}, {"data": ["GET /health", 985, 0, 0.0, 323.62944162436594, 3, 764, 334.0, 515.4, 588.0999999999998, 735.14, 11.240699319852101, 2.436948485358561, 4.1054897906491075], "isController": false}, {"data": ["GET /logs", 833, 0, 0.0, 646.937575030012, 31, 1037, 651.0, 785.6000000000001, 862.3, 982.1799999999993, 10.707491387732018, 241.07540424234534, 4.098961546866162], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8338, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
