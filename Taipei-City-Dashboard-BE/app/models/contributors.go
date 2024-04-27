package models

/* ----- Models ----- */

type Contributor struct {
	ID 			int		`json:"id" gorm:"column:id;autoincrement;primeryKey"` // id
	Name		string	`json:"name" gorm:"column:name;typpe:varchar"` // Name to show on FE
	ProfileLink	string	`json:"link" gorm:"column:link;type:varchar"` // url for hyperlink 
	ImageLink	string	`json:"image" gorm:"column:image;type:varchar"` // url for avatar image
}

/* ----- Handlers ----- */

func GetAllContributors(pageSize int, pageNum int, sort string, order string, searchByID string, searchByName string) (contributors []Contributor, totalContributors int64, resultNum int64, err error) {
	tempDB := DBManager.Table("contributors")

	// Count the total amount of contributors
	tempDB.Count(&totalContributors)

	// Search contributors
	if searchByID != "" {
		tempDB = tempDB.Where("id = ?", searchByID)
	}
	if searchByName != "" {
		tempDB = tempDB.Where("name LIKE ?", "%"+searchByName+"%")
	}

	// Get total
	err = tempDB.Count(&resultNum).Error
	if err != nil {
		return contributors, 0, 0, err
	}

	// Sort
	if sort != "" {
		tempDB = tempDB.Order(sort + " " + order)
	}

	// Paginate 
	if pageSize > 0 {
		tempDB = tempDB.Limit(pageSize)
		if pageNum > 0 {
			tempDB = tempDB.Offset((pageNum - 1) * pageSize)
		}
	}

	// Get the contributors
	err = tempDB.Find(&contributors).Error
	if err != nil {
		return contributors, 0, 0, err
	}

	// Return the contributors, total number of contributors, number of results, and nil error.
	return contributors, totalContributors, resultNum, nil
} 

func GetContributorByID(contributorID int) (contributor Contributor, err error) {
	err = DBManager.Table("contributors").Where("id = ?", contributorID).First(&contributor).Error
	if err != nil {
		return contributor, nil
	}
	return contributor, nil
}

func AddContributor(name string, profileLink string, imageLink string) (contributor Contributor, err error) {
	contributor.Name = name
	contributor.ProfileLink = profileLink
	contributor.ImageLink = imageLink

	err = DBManager.Create(&contributor).Error
	return contributor, err
}

func UpdateContributor(id int, name string, profileLink string, imageLink string) (contributor Contributor, err error) {
	contributor.Name = name
	contributor.ProfileLink = profileLink
	contributor.ImageLink = imageLink
	err = DBManager.Table("contributors").Where("id = ?", id).Updates(&contributor).Error
	return contributor, err
}

func DeleteContributor(id int) error {
	// Start a transaction to ensure data integrity.
	tx := DBManager.Begin()

	// Find the contributor with given id
	var contributor Contributor
	result := tx.Where("id = ?", id).First(&contributor)
	if result.Error != nil {
		// If the contributor is not found, rollback the transaction and return the error.
		tx.Rollback()
		return result.Error
	}

	// Delete the contributor
	if err := tx.Delete(&contributor).Error; err != nil {
		// If an error occurs during deletion, rollback the transaction and return the error.
		tx.Rollback()
		return err
	}

	// Commit the transaction if everything is successful.
	return tx.Commit().Error
}
