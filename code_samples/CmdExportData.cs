using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using ClosedXML.Excel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace ExampleNameSpace
{
    [Transaction(TransactionMode.Manual)]
    public class CmdExportData : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {

            string msBoxTitle = Properties.Resources.textPanDigiProQtyTitle + " - " + Properties.Resources.textBtnExcelTitle;
            msBoxTitle = msBoxTitle.Replace("\n", " ").Replace("\r", "");

            string path = Environment.GetFolderPath(Environment.SpecialFolder.Desktop) + "\\";
            string filename = ($"{DateTime.Now.ToString("yyyyMMddHHmm")}" + "Data.xlsx");
            string filepath = path + filename;

            SQLDataAccess dataAccess = new SQLDataAccess();
            dataAccess.CreateData();
            List<DataHistoryExport> dataDesignExportList = dataAccess.ExportDataToExcel();

            //Export List to Excel
            var wb = new XLWorkbook();
            var ws = wb.Worksheets.Add("DataExport");
            PropertyInfo[] properties = dataDesignExportList.First().GetType().GetProperties();
            List<string> headerNames = properties.Select(prop => prop.Name).ToList();
            for (int i = 0; i < headerNames.Count; i++)
            {
                ws.Cell(1, i + 1).Value = headerNames[i];
            }
            ws.Cell(2, 1).InsertData(dataExportList);
            wb.SaveAs(filepath);

            TaskDialog tbg = new TaskDialog("DigiProTaskDialog");
            tbg.Title = msBoxTitle;
            tbg.MainInstruction = "Extract Completed Successfully";
            tbg.MainContent = ("Quantities were successfully extracted and exported to the Desktop.");
            tbg.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Click here to open the below file: ", Environment.NewLine + filename);
            tbg.MainIcon = TaskDialogIcon.TaskDialogIconInformation;
            tbg.CommonButtons = TaskDialogCommonButtons.Close;
            
            TaskDialogResult tbgResult = tbg.Show();
            if (TaskDialogResult.CommandLink1 == tbgResult)
            {
                System.Diagnostics.Process.Start(@filepath);
            }

            return Result.Succeeded;

        }
    }
}

