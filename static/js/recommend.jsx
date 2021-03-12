"use strict"

const Recommendation = (prop) => {
  // const [bookIsUsers, setBookIsUsers] = React.useState(true)
  let { bookId } = useParams();
  const [show, setShow] = React.useState(false)
  let query = {
    'userId': prop.userId,
  }

  const getRecommendation = () => {
    fetch('/api/recommend', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(query)
    })
    .then(response => {
      // got rid of inner loop that only went to .then(data) if response populated
      return response.json()
    })
    .then(data => {
      prop.setBookResponse(data);
    })
  }

  const addBook = () => {
    
    fetch('/user/' + bookId + '/add', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      return response.json()
    })
    .then(data => {
      updateBook()
    })
  }

  const removeBook = () => {
    
    fetch('/user/' + bookId + '/delete', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      return response.json()
    })
    .then(data => {
      updateBook()
    })
  }

  React.useEffect(() => {
    getRecommendation();
  }, [])

  if (prop.bookResponse == null){
    return (
      <div>
        Some error has occurred. Response is null. This should not happen.
      </div>
    )
  }else{
    const book = prop.bookResponse.book;
    if (book == null) {
      return (
        <div>
          An error occurred with your recommendation.
          Error: {book.error}
        </div>
      )
    } else {
      const bookIsUsers = book.isUsers;
      return (
        <Container className="book-big-container">
          <Row className="justify-content-center">
            <Col md={8} className={bookIsUsers ? "book-big myBook w-100" : "book-big w-100"}>
              <div className="add-remove-container">
                {bookIsUsers 
                  ? (<label className="remove-book">
                      Remove Book
                      <button className="book-add-remove" onClick={removeBook}>
                        <i className="fas fa-minus"></i>
                      </button>
                    </label>) 
                  : <label>
                      Add Book
                      <button className="book-add-remove" onClick={addBook}>
                        <i className="fas fa-plus"></i>
                      </button> 
                    </label>
                }
              </div>
              <div className="title">
                {book.title}
              </div>
              <div>
                <img className="book-image-big" src={book.image ? book.image : '/static/img/BookPlaceholder.png'}/>
              </div>
              <div className="authors">
                {book.authors ? book.authors.map(author =>
                  (<div key={author}>{author}</div>)) : ''
                }
              </div>

              {book.description ? (<div className="text-left book-desc"><b>Description: </b>{book.description} </div>) : ''}

              {book.publisher ? (<div className="text-left">Publisher: {book.publisher} </div>) : ''}

              {book.year ? (<div className="text-left">Publication Year: {book.year} </div>) : ''}

              {book.isbn ? (<div className="text-left">ISBN: {book.isbn}</div>) : ''}

              <Container>
                <Row>
                  <Col sm={6}>
                    <div className="tags w-100">
                      <div className="center-text">General Tags:</div>
                      {book.tags ? (
                        <span>{book.tags.map(tag =>
                          (<Badge pill variant="info" className="tag-button"key={tag}>{tag}</Badge>))}</span>
                          ) : ''
                        }
                    </div>
                  </Col>
                  <Col sm={6}>
                    <div className="tags w-100">
                      <div className="center-text">Your Tags:</div>
                      {book.tags ? (
                        <span>{book.tags.map(tag =>
                          (<Badge pill variant="info" className="tag-button"key={tag}>{tag}</Badge>))}</span>
                          ) : ''
                        }
                    </div>
                  </Col>
                </Row>
              </Container>
              
              <div className="rating">Average Rating: {book.avgRating}</div>

            
              {bookIsUsers 
                ? <Container className="rating-user">
                    <Row> 
                      <b>Your rating:</b> {book.userScore}
                    </Row>
                    <Row className="text-left">
                      <b>Your review:</b> {book.userReview}
                    </Row>
                    <Row>
                      <Col sm={{span: 6, offset: 6}}>
                        <button className="button-rating-add" onClick={handleShow}>
                          {book.userScore ? "Update rating/review" : "Add rating/review"}
                        </button>
                      </Col>
                    </Row>
                  </Container>
                : ''
              }
            </Col>
        </Row>
      </Container>
      )
    }
  }
}