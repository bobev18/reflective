 * Branch and test
   - Django 1.6 - official release = IN PROGRESS
   - MySQL connectors = DONE
 * Complete The Django Book
 * Refactoring
   - TDD
   - data consistency (tools)
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
 * 
