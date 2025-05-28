import test_case_extractor as tce
import test_file_extractor as tfe
import classification_functions as cf
import helper_functions as h


def main():
    #---------------------------------------------
    Low = 1
    Medium = 2
    High = 3
    DisableClassification = 4

    #Change this value to your prefered strictness.
    strictness = Low

    #Change these file paths if needed.
    #Dataset folder.
    projects_root_dir = r".\..\dataset" 
    #Results folder. (feel free to change the name of the csv file if desired)
    result_file_dir = r".\..\results\result.csv" 

    #---------------------------------------------

    print("Starting Process")
    print("Creating (or accessing) CSV File")
    try:
        h.create_csv_file(result_file_dir)
    except Exception as e:
        print(f"failed to create or access CSV file: {e}")
        return

    print("Extracting Test Files")
    try:
        all_test_file_info = tfe.scan_all_projects(projects_root_dir)
    except Exception as e:
        print(f"Failed to scan all test files: {e}")
        return
    
    print("Extracting and Classifying Test Cases For Each File:")
    file_count = len(all_test_file_info)
    last_percent_reported = -1

    for index, file in enumerate(all_test_file_info, start=1):
        percent = int((index / file_count) * 100)
        if percent != last_percent_reported:
            print(f"{percent}%")
        last_percent_reported = percent
        try:
            file_path = file[2]
            project_name = file[0]
            file_name = file[1]
            tests = tce.find_hypothesis_tests(file_path)
            for test_case in tests:
                try:
                    cf.analyse_test_case(strictness, result_file_dir, test_case, file_name, project_name, file_path)
                except Exception as e:
                    print(f"Error analyzing test case in {file_path}: {e}")
        except Exception as e:
            print(f"Error processing file info {file}: {e}")
    print("Done")

main()