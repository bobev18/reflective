 * Branch and test
   - Django 1.6 - official release = IN PROGRESS
   - MySQL connectors = DONE
 * Complete The Django Book = DONE
 * Refactoring
   - TDD
   - data consistency (tools)
     ~ linking to single DB is a start
       1. deploy the DB in own folder
       2. run sched recapture
         ###%%#$$# need the TDD in place so change of sched recapture code can properly update the DB values of cases, affected by change in shift
   - improve speed (i.e. more strict filtration on periods)
   - post support times to the RSL SFDC
 * Weekly
   - change weekly to integrate the results from the last week run
   - fix the checks for SLA & reply time, to accout for user comments during the off hours
   - cases 10668 & 2265 did not show in weekly 6-13 Nov :: fix the Case.update method to use target time against "closed" time, and not only against "created". This should include every case that had status "open" during the target period
 * License form
   - limit send if radio button 2 or 4 are selected
   - more strict validation of the HostID
 * Add Email model -- analogus to the Comments
 * Add Report model -- data from any kind of report can be saved and edited
 * add Handover form
 * Move common methods (like "clear_bad_chars") to module "utils"
 *
 * move "detect environmet" snippet to the settings file
 * make Comments act more like an object = to keep the results internally, instead of returning them, and later to pull them again upon save
 * consolidate CONSTANTS
 