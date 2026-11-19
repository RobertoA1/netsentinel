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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.03836679394014041, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.315, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.06573033707865168, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.026713124274099883, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.008433734939759036, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.1041890440386681, 500, 1500, "GET /health"], "isController": false}, {"data": [0.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7520, 0, 0.0, 2826.2166223404197, 6, 5628, 2658.0, 4171.900000000001, 4689.95, 5371.79, 81.60607704829083, 389.1930933769669, 30.472088222327724], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 804, 0, 0.0, 2985.5870646766216, 1720, 5628, 2728.5, 4185.5, 4678.25, 5415.700000000001, 9.597478871221888, 1.5839589152700184, 3.7302701081506946], "isController": false}, {"data": ["GET /findings", 769, 0, 0.0, 2855.8803641092327, 1814, 5597, 2624.0, 3591.0, 4205.0, 5333.199999999994, 10.186239966090021, 230.51341673262112, 4.088422486389647], "isController": false}, {"data": ["POST /auth/login", 400, 0, 0.0, 2626.7974999999988, 81, 5603, 2755.0, 5270.3, 5355.75, 5533.9, 15.658641612840086, 33.549862986885884, 3.7311606968095514], "isController": false}, {"data": ["GET /auth/me", 890, 0, 0.0, 2667.8337078651657, 14, 5578, 2531.5, 4088.6999999999994, 4693.149999999995, 5415.63, 9.980935292138613, 16.4724420348772, 3.6551276704609172], "isController": false}, {"data": ["GET /dashboard/summary", 861, 0, 0.0, 3094.5214866434394, 66, 5590, 3069.0, 4544.8, 4802.9, 5521.14, 9.802805355679023, 5.628954637831315, 3.6856250604847896], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 830, 0, 0.0, 3075.956626506027, 871, 5540, 3011.5, 4229.099999999999, 4595.049999999999, 5332.589999999999, 9.626536766411505, 1.5887546030503363, 3.7227622651356995], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 800, 0, 0.0, 2805.993749999998, 1751, 5526, 2498.0, 3972.899999999999, 4531.049999999998, 5322.88, 10.132097217472802, 3.2157535114049423, 3.938061223197437], "isController": false}, {"data": ["GET /alerts/unread-count", 577, 0, 0.0, 2694.733102253036, 1806, 4703, 2614.0, 3281.4000000000005, 3534.2, 4514.1, 9.086184904650175, 1.5971809402705384, 3.4339390215816574], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 599, 0, 0.0, 25932.973288814705, 17923, 29889, 25730.0, 29284.0, 29517.0, 29780.0, 7.4945261182358465, 362.75547632546136, 25.62912984829528], "isController": true}, {"data": ["GET /health", 931, 0, 0.0, 2458.470461868959, 6, 5203, 2339.0, 4246.600000000001, 4936.999999999999, 5132.68, 10.287520166191518, 2.230302223529802, 3.757355998198855], "isController": false}, {"data": ["GET /logs", 658, 0, 0.0, 2926.3753799392116, 1854, 4908, 2751.0, 3608.6000000000004, 4152.599999999999, 4792.079999999997, 9.57731718677224, 215.62992943460353, 3.6663167355612485], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 7520, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
