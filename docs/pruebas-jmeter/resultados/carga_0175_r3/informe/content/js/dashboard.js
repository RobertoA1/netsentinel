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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.8473217331968611, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9423963133640553, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.8777239709443099, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9914285714285714, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9470588235294117, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9117971334068358, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.93954802259887, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9361702127659575, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9355246523388117, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.03598014888337469, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9862433862433863, 500, 1500, "GET /health"], "isController": false}, {"data": [0.861557478368356, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7987, 0, 0.0, 241.2759484161765, 2, 1028, 177.0, 570.0, 685.0, 847.1199999999999, 90.1009645214056, 454.02732193722153, 34.055619059873656], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 868, 0, 0.0, 232.37327188940094, 8, 936, 183.5, 535.1, 637.0, 851.9599999999991, 10.644821073802458, 1.7568112905006008, 4.137342565794315], "isController": false}, {"data": ["GET /findings", 826, 0, 0.0, 321.76029055690066, 10, 1025, 259.5, 724.6000000000001, 816.2499999999999, 937.2200000000003, 10.515595162316997, 237.96668622692553, 4.220614855187779], "isController": false}, {"data": ["POST /auth/login", 175, 0, 0.0, 158.22857142857134, 54, 590, 96.0, 343.80000000000007, 381.39999999999986, 583.9200000000001, 8.543253270845538, 18.304587574448348, 2.035697068443663], "isController": false}, {"data": ["GET /auth/me", 935, 0, 0.0, 210.91978609625664, 5, 864, 144.0, 506.4, 617.0, 723.9599999999998, 10.889440154664989, 17.971829942757648, 3.987832087890011], "isController": false}, {"data": ["GET /dashboard/summary", 907, 0, 0.0, 268.6108048511574, 10, 956, 212.0, 608.2, 720.7999999999997, 847.92, 10.74313600075806, 6.168910125435293, 4.039167344035013], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 885, 0, 0.0, 229.6000000000001, 9, 966, 170.0, 528.4, 647.6999999999999, 851.8199999999998, 10.682342148780283, 1.7630037335389332, 4.1310620028486245], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 846, 0, 0.0, 241.19858156028374, 8, 916, 196.0, 541.2000000000003, 639.0, 799.53, 10.568526777348875, 3.3542687525765467, 4.107689118539894], "isController": false}, {"data": ["GET /alerts/unread-count", 791, 0, 0.0, 234.26548672566375, 6, 897, 177.0, 555.0, 618.4, 799.5600000000003, 10.57175696987517, 1.8583166548608698, 3.99538080795087], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 806, 0, 0.0, 2224.156327543424, 620, 3671, 2286.0, 2765.3, 2933.6, 3142.879999999999, 10.532643353719095, 509.842168592533, 36.090737770993414], "isController": true}, {"data": ["GET /health", 945, 0, 0.0, 129.4000000000002, 2, 736, 74.0, 353.4, 458.69999999999993, 564.6999999999998, 10.845862504303915, 2.3513490976127627, 3.961281813095375], "isController": false}, {"data": ["GET /logs", 809, 0, 0.0, 341.4462299134737, 21, 1028, 296.0, 728.0, 812.0, 946.2999999999998, 10.525220196973837, 236.97163246214043, 4.029185856654047], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 7987, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
