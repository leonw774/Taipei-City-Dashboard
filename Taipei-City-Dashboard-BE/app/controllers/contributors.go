package controllers

import (
	"TaipeiCityDashboardBE/app/models"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
)


type contributorQuery struct {
	PageSize     int    `form:"pagesize"`
	PageNum      int    `form:"pagenum"`
	Sort		 string	`form:"sort"`
	Order		 string `form:"order"`
	SearchByID   string `form:"searchbyid"`
	SearchByName string `form:"searchbyname"`
}

/*
GetAllContributors
GET /api/v1/ccontributor
*/
func GetAllContributors(c *gin.Context) {
	var contributors []models.Contributor
	var totalContributors int64
	var resultNum int64

	// Get query parameter
	var query contributorQuery
	c.ShouldBindQuery(&query)
	fmt.Printf("%+v\n", query)

	contributors, totalContributors, resultNum, err := models.GetAllContributors(query.PageSize, query.PageNum, query.Sort, query.Order, query.SearchByID, query.SearchByName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "total": totalContributors, "results": resultNum, "data": contributors})
}

/*
AddContributor adds a new contributor
POST /api/v1/contributor
*/
func AddContributor(c *gin.Context) {
	var contributor models.Contributor

	// Bind the JSON body
	if err := c.ShouldBindJSON(&contributor); err != nil  {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Check required field
	if contributor.Name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "name info is required"})
		return
	}

	contributor, err := models.AddContributor(contributor.Name, contributor.ProfileLink, contributor.ImageLink)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": contributor})
}

/*
UpdateContributor modifies a contributor by ID
PATCH /api/v1/contributor/:id
*/
func UpdateContributor(c *gin.Context) {
	// Check if contributor exists
	contributorID := c.Param("id")
	contributor, err := models.GetContributorByID(contributorID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No contributor found"})
		return
	}

	// Bind the JSON body
	if err := c.ShouldBindJSON(&contributor); err != nil  {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": err.Error()})
		return
	}

	// Check required field
	if contributor.Name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "error", "message": "name info is required"})
		return
	}

	contributor, err = models.UpdateContributor(contributorID, contributor.Name, contributor.ProfileLink, contributor.ImageLink)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "error", "message": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "success", "data": contributor})
}