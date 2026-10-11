import os
import time
from html import escape
from urllib.parse import parse_qs

import psycopg


def wrapBody(body, title="Blank Title"):
  return (
    "<html>\n"
    "<head>\n"
    f"<title>{title}</title>\n"
    "</head>\n"
    "<body>\n"
    f"{body}\n"
    "<hr>\n"
    f"<p>This page was generated at {time.ctime()}.</p>\n"
    "</body>\n"
    "</html>\n"
  )


def showMainMenu():
  return """
    <h2>University Database</h2>
    <FORM METHOD="POST" action="university.py">
    <p><INPUT TYPE="SUBMIT" NAME="showStudents" VALUE="Students"></p>
    <p><INPUT TYPE="SUBMIT" NAME="showCourses" VALUE="Courses"></p>
    <p><INPUT TYPE="SUBMIT" NAME="showRooms" VALUE="Rooms"></p>
    <p><INPUT TYPE="SUBMIT" NAME="showEnrollments" VALUE="Enrollments"></p>
    </FORM>
    """


def showActionMenu(entity):
  # entity is carried along in a hidden field so later steps know
  # which table the Add/Update/Delete/Display buttons apply to
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>%s</h2>
    <FORM METHOD="POST" action="university.py">
    <INPUT TYPE="HIDDEN" NAME="entity" VALUE="%s">
    <p><INPUT TYPE="SUBMIT" NAME="add" VALUE="Add"></p>
    <p><INPUT TYPE="SUBMIT" NAME="update" VALUE="Update"></p>
    <p><INPUT TYPE="SUBMIT" NAME="delete" VALUE="Delete"></p>
    <p><INPUT TYPE="SUBMIT" NAME="display" VALUE="Display"></p>
    </FORM>
    """ % (
    entity,
    entity,
  )

def get_qs_post(env):
  """
  :param env: WSGI environment
  :returns: A tuple (qs, post), containing the query string and post data,
            respectively
  """
  try:
    request_body_size = int(env.get("CONTENT_LENGTH", 0))
  except ValueError:
    request_body_size = 0
  request_body = env["wsgi.input"].read(request_body_size).decode("utf-8")
  post = parse_qs(request_body)
  return parse_qs(env["QUERY_STRING"]), post

"""
STUDENT FUNCTIONS
"""

def showAddStudentForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Add A Student</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Name</td>
            <td><INPUT TYPE="TEXT" NAME="name" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="addStudent" VALUE="Add!"></td>
        </tr>
    </table>
    </FORM>
    """


def addStudent(conn, name):
  """
  Inserts a new student. Returns (body, succeeded).
  """
  name = name.strip()
  if not name:
    return "<p>Error: name cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM student")
    nextID = cursor.fetchone()[0]

    cursor.execute("INSERT INTO student (id, name) VALUES (%s,%s)", (nextID, name))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Add Student Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = f"""
    <p>Add Student Succeeded.</p>
    <table border=1>
        <tr>
            <td>ID</td>
            <td>{nextID}</td>
        </tr>
        <tr>
            <td>Name</td>
            <td>{escape(name)}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showUpdateStudentIdForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Update A Student</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="idNum" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectStudent" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getUpdateStudentForm(conn, idText):
  """
  Looks up the student and returns (body, succeeded). On success the body
  is a form pre-filled with the current name.
  """
  try:
    idNum = int(idText)
  except ValueError:
    return "<p>Error: ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT id, name FROM student WHERE id=%s", (idNum,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no student found with ID {idNum}.</p>", False

  idNum, name = data
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Update Student {idNum}</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Name</td>
            <td><INPUT TYPE="TEXT" NAME="name" VALUE="{escape(name)}"></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <INPUT TYPE="HIDDEN" NAME="idNum" VALUE="{idNum}">
            <INPUT TYPE="SUBMIT" NAME="completeStudentUpdate" VALUE="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """
  return body, True


def updateStudent(conn, idText, name):
  """
  Updates a student's name. Returns (body, succeeded).
  """
  name = name.strip()
  if not name:
    return "<p>Error: name cannot be empty.</p>", False

  try:
    idNum = int(idText)
  except ValueError:
    return "<p>Error: ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("UPDATE student SET name=%s WHERE id=%s", (name, idNum))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Update Student Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Update Student Failed. No student with ID {idNum}.</p>", False

  body = f"""
    <p>Update Student Succeeded.</p>
    <table border=1>
        <tr>
            <td>ID</td>
            <td>{idNum}</td>
        </tr>
        <tr>
            <td>Name</td>
            <td>{escape(name)}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showDeleteStudentIdForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Delete A Student</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="idNum" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectStudentDelete" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getDeleteStudentConfirm(conn, idText):
  """
  Looks up the student and returns (body, succeeded). On success the body
  shows the student and asks for confirmation.
  """
  try:
    idNum = int(idText)
  except ValueError:
    return "<p>Error: ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT id, name FROM student WHERE id=%s", (idNum,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no student found with ID {idNum}.</p>", False

  idNum, name = data
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Delete Student {idNum}</h2>
    <p>Are you sure you want to delete this student?</p>
    <table border=1>
        <tr>
            <td>ID</td>
            <td>{idNum}</td>
        </tr>
        <tr>
            <td>Name</td>
            <td>{escape(name)}</td>
        </tr>
    </table>
    <FORM METHOD="POST" action="university.py">
    <INPUT TYPE="HIDDEN" NAME="idNum" VALUE="{idNum}">
    <p><INPUT TYPE="SUBMIT" NAME="confirmStudentDelete" VALUE="Yes, Delete"></p>
    </FORM>
    <p><a href="./university.py">No, cancel.</a></p>
    """
  return body, True


def deleteStudent(conn, idText):
  """
  Deletes a student. Returns (body, succeeded).
  """
  try:
    idNum = int(idText)
  except ValueError:
    return "<p>Error: ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("DELETE FROM student WHERE id=%s", (idNum,))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Delete Student Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Delete Student Failed. No student with ID {idNum}.</p>", False

  body = f"""
    <p>Delete Student Succeeded. Student {idNum} was deleted.</p>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showAllStudents(conn):
  """
  Returns (body, succeeded). On success the body is a table of all students.
  """
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT id, name FROM student ORDER BY id")
    data = cursor.fetchall()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Display Students Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = """
    <a href="./university.py">Return to main page.</a>
    <h2>Student List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1><b>id</b></font></td>
        <td><font size=+1><b>name</b></font></td>
      </tr>
    """

  # each iteration of this loop creates one row of output:
  for idNum, name in data:
    body += f"<tr><td>{idNum}</td><td>{escape(name)}</td></tr>\n"

  body += f"</table><p>Found {len(data)} students.</p>"
  return body, True


"""
COURSES FUNCTIONS
"""

def showAddCourseForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Add A Course</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Number (e.g. CSCI 220)</td>
            <td><INPUT TYPE="TEXT" NAME="number" VALUE=""></td>
        </tr>
        <tr>
            <td>Title</td>
            <td><INPUT TYPE="TEXT" NAME="title" VALUE=""></td>
        </tr>
        <tr>
            <td>Room (e.g. MACD 117, optional)</td>
            <td><INPUT TYPE="TEXT" NAME="room" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="addCourse" VALUE="Add!"></td>
        </tr>
    </table>
    </FORM>
    """


def addCourse(conn, number, title, room):
  """
  Inserts a new course. Returns (body, succeeded).
  """
  number = number.strip().upper()
  title = title.strip()
  room = room.strip().upper() or None  # blank means "no room"

  if not number or not title:
    return "<p>Error: course number and title cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute(
      "INSERT INTO course (number, title, room) VALUES (%s,%s,%s)",
      (number, title, room),
    )
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Add Course Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = f"""
    <p>Add Course Succeeded.</p>
    <table border=1>
        <tr>
            <td>Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Title</td>
            <td>{escape(title)}</td>
        </tr>
        <tr>
            <td>Room</td>
            <td>{escape(room or "None")}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showUpdateCourseNumberForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Update A Course</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Course Number</td>
            <td><INPUT TYPE="TEXT" NAME="number" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectCourse" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getUpdateCourseForm(conn, numberText):
  """
  Looks up the course and returns (body, succeeded). On success the body
  is a form pre-filled with the current title and room.
  """
  number = numberText.strip().upper()
  if not number:
    return "<p>Error: course number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, title, room FROM course WHERE number=%s", (number,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no course found with number {escape(number)}.</p>", False

  number, title, room = data
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Update Course {escape(number)}</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Title</td>
            <td><INPUT TYPE="TEXT" NAME="title" VALUE="{escape(title or '')}"></td>
        </tr>
        <tr>
            <td>Room</td>
            <td><INPUT TYPE="TEXT" NAME="room" VALUE="{escape(room or '')}"></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <INPUT TYPE="HIDDEN" NAME="number" VALUE="{escape(number)}">
            <INPUT TYPE="SUBMIT" NAME="completeCourseUpdate" VALUE="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """
  return body, True


def updateCourse(conn, numberText, title, room):
  """
  Updates a course's title and room. Returns (body, succeeded).
  The course number is not editable, because enrollments refer to it.
  """
  number = numberText.strip().upper()
  title = title.strip()
  room = room.strip().upper() or None

  if not title:
    return "<p>Error: title cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute(
      "UPDATE course SET title=%s, room=%s WHERE number=%s",
      (title, room, number),
    )
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Update Course Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Update Course Failed. No course with number {escape(number)}.</p>", False

  body = f"""
    <p>Update Course Succeeded.</p>
    <table border=1>
        <tr>
            <td>Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Title</td>
            <td>{escape(title)}</td>
        </tr>
        <tr>
            <td>Room</td>
            <td>{escape(room or "None")}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showDeleteCourseNumberForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Delete A Course</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Course Number</td>
            <td><INPUT TYPE="TEXT" NAME="number" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectCourseDelete" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getDeleteCourseConfirm(conn, numberText):
  """
  Looks up the course and returns (body, succeeded). On success the body
  shows the course and asks for confirmation.
  """
  number = numberText.strip().upper()
  if not number:
    return "<p>Error: course number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, title, room FROM course WHERE number=%s", (number,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no course found with number {escape(number)}.</p>", False

  number, title, room = data
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Delete Course {escape(number)}</h2>
    <p>Are you sure you want to delete this course?</p>
    <table border=1>
        <tr>
            <td>Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Title</td>
            <td>{escape(title or "")}</td>
        </tr>
        <tr>
            <td>Room</td>
            <td>{escape(room or "None")}</td>
        </tr>
    </table>
    <FORM METHOD="POST" action="university.py">
    <INPUT TYPE="HIDDEN" NAME="number" VALUE="{escape(number)}">
    <p><INPUT TYPE="SUBMIT" NAME="confirmCourseDelete" VALUE="Yes, Delete"></p>
    </FORM>
    <p><a href="./university.py">No, cancel.</a></p>
    """
  return body, True


def deleteCourse(conn, numberText):
  """
  Deletes a course. Returns (body, succeeded).
  """
  number = numberText.strip().upper()
  if not number:
    return "<p>Error: course number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("DELETE FROM course WHERE number=%s", (number,))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Delete Course Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Delete Course Failed. No course with number {escape(number)}.</p>", False

  body = f"""
    <p>Delete Course Succeeded. Course {escape(number)} was deleted.</p>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showAllCourses(conn):
  """
  Returns (body, succeeded). On success the body is a table of all courses.
  """
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, title, COALESCE(room, 'None') FROM course ORDER BY number")
    data = cursor.fetchall()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Display Courses Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = """
    <a href="./university.py">Return to main page.</a>
    <h2>Course List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1><b>number</b></font></td>
        <td><font size=+1><b>title</b></font></td>
        <td><font size=+1><b>room</b></font></td>
      </tr>
    """

  # each iteration of this loop creates one row of output:
  for number, title, room in data:
    body += f"<tr><td>{escape(number)}</td><td>{escape(title or '')}</td><td>{escape(room)}</td></tr>\n"

  body += f"</table><p>Found {len(data)} courses.</p>"
  return body, True

""" 
ENROLLMENTS FUNCTIONS
"""

def showAddEnrollmentForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Add An Enrolled</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="student" VALUE=""></td>
        </tr>
        <tr>
            <td>Course ID</td>
            <td><INPUT TYPE="TEXT" NAME="course" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="addEnrollment" VALUE="Add"></td>
        </tr>
    </table>
    </FORM>
    """
    
def addEnrollment(conn, student, course):
  """
  Inserts a new enrolled. Returns (body, succeeded).
  """
  student = student.strip()
  course = course.strip().upper()
  
  if not student or not course:
    return "<p>Error: Student ID and Course ID cannot be empty.</p>", False

  try:
    studentId = int(student)
  except ValueError:
    return "<p>Error: Student ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("INSERT INTO enrolled (student, course) VALUES (%s,%s)", (studentId, course))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Add Enrolled Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = f"""
    <p>Add Enrolled Succeeded.</p>
    <table border=1>
        <tr>
            <td>Student ID</td>
            <td>{escape(student)}</td>
        </tr>
        <tr>
            <td>Course ID</td>
            <td>{escape(course)}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True
    
  
def showupdateEnrollmentForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Update An Enrolled</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="student" VALUE=""></td>
        </tr>
        <tr>
          <td>Current Course ID</td>
          <td><INPUT TYPE="TEXT" NAME="currentCourse" VALUE=""></td>
        </tr>
        <tr>
          <td>New Course ID</td>
          <td><INPUT TYPE="TEXT" NAME="newCourse" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="updateEnrollment" VALUE="Update"></td>
        </tr>
    </table>
    </FORM>
    """
    
    
def updateEnrollment(conn, student, currentCourse, newCourse):
  """
  Updates an enrolled. Returns (body, succeeded).
  """
  student = student.strip()
  currentCourse = currentCourse.strip().upper()
  newCourse = newCourse.strip().upper()
  
  if not student or not currentCourse or not newCourse:
    return "<p>Error: Student ID, current course ID, and new course ID cannot be empty.</p>", False

  try:
    studentId = int(student)
  except ValueError:
    return "<p>Error: Student ID must be a whole number.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute(
      "UPDATE enrolled SET course=%s WHERE student=%s AND course=%s",
      (newCourse, studentId, currentCourse),
    )
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Update Enrolled Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Update Enrolled Failed. No enrollment found for Student ID {student} and Course ID {currentCourse}.</p>", False

  body = f"""
    <p>Update Enrolled Succeeded.</p>
    <table border=1>
        <tr>
            <td>Student ID</td>
            <td>{escape(student)}</td>
        </tr>
        <tr>
            <td>Course ID</td>
          <td>{escape(newCourse)}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showDeleteEnrollmentForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Delete An Enrolled</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="student" VALUE=""></td>
        </tr>
        <tr>
            <td>Course ID</td>
            <td><INPUT TYPE="TEXT" NAME="course" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="deleteEnrollment" VALUE="Delete"></td>
        </tr>
    </table>
    </FORM>
    """ 
    
    
def deleteEnrollment(conn, student, course):
  """
  Deletes an enrolled. Returns (body, succeeded).
  """
  student = student.strip()
  course = course.strip().upper()
  
  if not student or not course:
    return "<p>Error: Student ID and Course ID cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("DELETE FROM enrolled WHERE student=%s AND course=%s", (int(student), course))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Delete Enrolled Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Delete Enrolled Failed. No enrolled with Student ID {student} and Course ID {course}.</p>", False

  body = f"""
    <p>Delete Enrolled Succeeded. Enrolled with Student ID {escape(student)} and Course ID {escape(course)} was deleted.</p>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showAllEnrollments(conn):
  """
  Returns (body, succeeded). On success the body is a table of all enrollments.
  """
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT student, course FROM enrolled ORDER BY student")
    data = cursor.fetchall()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Display Enrollments Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = """
    <a href="./university.py">Return to main page.</a>
    <h2>enrolled List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1><b>Student ID</b></font></td>
        <td><font size=+1><b>Course ID</b></font></td>
      </tr>
    """

  # each iteration of this loop creates one row of output:
  for student, course in data:
    body += f"<tr><td>{student}</td><td>{escape(course)}</td></tr>\n"

  body += f"</table><p>Found {len(data)} enrollments.</p>"
  return body, True


"""
ROOM FUNCTIONS
"""

def parseCapacity(capacityText):
  """
  Returns (capacity, error). error is None when the text is a valid capacity.
  """
  try:
    capacity = int(capacityText.strip())
  except ValueError:
    return None, "<p>Error: capacity must be a whole number.</p>"
  if capacity < 0:
    return None, "<p>Error: capacity cannot be negative.</p>"
  return capacity, None


def showAddRoomForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Add A Room</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Room Number</td>
            <td><INPUT TYPE="TEXT" NAME="roomNumber" VALUE=""></td>
        </tr>
        <tr>
            <td>Capacity</td>
            <td><INPUT TYPE="TEXT" NAME="capacity" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="addRoom" VALUE="Add!"></td>
        </tr>
    </table>
    </FORM>
    """


def addRoom(conn, number, capacityText):
  """
  Inserts a new room. Returns (body, succeeded).
  """
  number = number.strip().upper()
  if not number:
    return "<p>Error: room number cannot be empty.</p>", False

  capacity, error = parseCapacity(capacityText)
  if error:
    return error, False

  cursor = conn.cursor()
  try:
    cursor.execute("INSERT INTO room (number, capacity) VALUES (%s,%s)", (number, capacity))
    conn.commit()
  except psycopg.errors.UniqueViolation:
    conn.rollback()
    return f"<p>Add Room Failed. Room {escape(number)} already exists.</p>", False
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Add Room Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = f"""
    <p>Add Room Succeeded.</p>
    <table border=1>
        <tr>
            <td>Room Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Capacity</td>
            <td>{capacity}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showUpdateRoomNumberForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Update A Room</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Room Number</td>
            <td><INPUT TYPE="TEXT" NAME="roomNumber" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectRoom" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getUpdateRoomForm(conn, number):
  """
  Looks up the room and returns (body, succeeded). On success the body
  is a form pre-filled with the current capacity.
  """
  number = number.strip().upper()
  if not number:
    return "<p>Error: room number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, capacity FROM room WHERE number=%s", (number,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no room found with number {escape(number)}.</p>", False

  number, capacity = data
  if capacity is None:
    capacity = ""
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Update Room {escape(number)}</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Capacity</td>
            <td><INPUT TYPE="TEXT" NAME="capacity" VALUE="{capacity}"></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <INPUT TYPE="HIDDEN" NAME="roomNumber" VALUE="{escape(number)}">
            <INPUT TYPE="SUBMIT" NAME="completeRoomUpdate" VALUE="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """
  return body, True


def updateRoom(conn, number, capacityText):
  """
  Updates a room's capacity. Returns (body, succeeded).
  """
  number = number.strip().upper()
  if not number:
    return "<p>Error: room number cannot be empty.</p>", False

  capacity, error = parseCapacity(capacityText)
  if error:
    return error, False

  cursor = conn.cursor()
  try:
    cursor.execute("UPDATE room SET capacity=%s WHERE number=%s", (capacity, number))
    conn.commit()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Update Room Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Update Room Failed. No room with number {escape(number)}.</p>", False

  body = f"""
    <p>Update Room Succeeded.</p>
    <table border=1>
        <tr>
            <td>Room Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Capacity</td>
            <td>{capacity}</td>
        </tr>
    </table>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showDeleteRoomNumberForm():
  return """
    <a href="./university.py">Return to main page.</a>
    <h2>Delete A Room</h2>
    <p>
    <FORM METHOD="POST" action="university.py">
    <table>
        <tr>
            <td>Room Number</td>
            <td><INPUT TYPE="TEXT" NAME="roomNumber" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td><INPUT TYPE="SUBMIT" NAME="selectRoomDelete" VALUE="Find!"></td>
        </tr>
    </table>
    </FORM>
    """


def getDeleteRoomConfirm(conn, number):
  """
  Looks up the room and returns (body, succeeded). On success the body
  shows the room and asks for confirmation.
  """
  number = number.strip().upper()
  if not number:
    return "<p>Error: room number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, capacity FROM room WHERE number=%s", (number,))
    data = cursor.fetchone()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Lookup Failed.</p><p>Error: {escape(str(e))}</p>", False

  if data is None:
    return f"<p>Error: no room found with number {escape(number)}.</p>", False

  number, capacity = data
  if capacity is None:
    capacity = ""
  body = f"""
    <a href="./university.py">Return to main page.</a>
    <h2>Delete Room {escape(number)}</h2>
    <p>Are you sure you want to delete this room?</p>
    <table border=1>
        <tr>
            <td>Room Number</td>
            <td>{escape(number)}</td>
        </tr>
        <tr>
            <td>Capacity</td>
            <td>{capacity}</td>
        </tr>
    </table>
    <FORM METHOD="POST" action="university.py">
    <INPUT TYPE="HIDDEN" NAME="roomNumber" VALUE="{escape(number)}">
    <p><INPUT TYPE="SUBMIT" NAME="confirmRoomDelete" VALUE="Yes, Delete"></p>
    </FORM>
    <p><a href="./university.py">No, cancel.</a></p>
    """
  return body, True


def deleteRoom(conn, number):
  """
  Deletes a room. Returns (body, succeeded).
  """
  number = number.strip().upper()
  if not number:
    return "<p>Error: room number cannot be empty.</p>", False

  cursor = conn.cursor()
  try:
    cursor.execute("DELETE FROM room WHERE number=%s", (number,))
    conn.commit()
  except psycopg.errors.ForeignKeyViolation:
    # a course still meets in this room, so the database refuses the delete
    conn.rollback()
    return (
      f"<p>Delete Room Failed. Room {escape(number)} is still assigned to a course. "
      "Move or delete those courses first.</p>"
    ), False
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Delete Room Failed.</p><p>Error: {escape(str(e))}</p>", False

  if cursor.rowcount == 0:
    return f"<p>Delete Room Failed. No room with number {escape(number)}.</p>", False

  body = f"""
    <p>Delete Room Succeeded. Room {escape(number)} was deleted.</p>
    <p><a href="./university.py">Return to main page.</a></p>
    """
  return body, True


def showAllRooms(conn):
  """
  Returns (body, succeeded). On success the body is a table of all rooms.
  """
  cursor = conn.cursor()
  try:
    cursor.execute("SELECT number, capacity FROM room ORDER BY number")
    data = cursor.fetchall()
  except psycopg.Error as e:
    conn.rollback()
    print(f"Database error: {e}")
    return f"<p>Display Rooms Failed.</p><p>Error: {escape(str(e))}</p>", False

  body = """
    <a href="./university.py">Return to main page.</a>
    <h2>Room List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1><b>number</b></font></td>
        <td><font size=+1><b>capacity</b></font></td>
      </tr>
    """

  # each iteration of this loop creates one row of output:
  for number, capacity in data:
    if capacity is None:
      capacity = ""
    body += f"<tr><td>{escape(number)}</td><td>{capacity}</td></tr>\n"

  body += f"</table><p>Found {len(data)} rooms.</p>"
  return body, True

  
def application(env, start_response):
  qs, post = get_qs_post(env)

  body = ""
  conn = None
  try:
    conn = psycopg.connect(
      host="postgres",
      dbname=os.environ["POSTGRES_DB"],
      user=os.environ["POSTGRES_USER"],
      password=os.environ["POSTGRES_PASSWORD"],
    )
  except psycopg.Error as e:
    print(f"Database error: {e}")
    body += "<p>Could not connect to the database. Check logs for DB error.</p>"

  if conn is None:
    pass
  elif "showStudents" in post:
    body += showActionMenu("Students")
  elif "showCourses" in post:
    body += showActionMenu("Courses")
  elif "showRooms" in post:
    body += showActionMenu("Rooms")
  elif "showEnrollments" in post:
    body += showActionMenu("Enrollments")
    
  ## STUDENT ROUTING  
  # Students > Add: show the form
  elif "add" in post and post.get("entity", [""])[0] == "Students":
    body += showAddStudentForm()
  # Students > Add: process the submitted form
  elif "addStudent" in post:
    b, ok = addStudent(conn, post.get("name", [""])[0])
    body += b
    if not ok:
      # show the form again so the user can retry
      body += showAddStudentForm()
  # Students > Update: ask for the id
  elif "update" in post and post.get("entity", [""])[0] == "Students":
    body += showUpdateStudentIdForm()
  # Students > Update: look up the id, show the form with the current name
  elif "selectStudent" in post:
    b, ok = getUpdateStudentForm(conn, post.get("idNum", [""])[0].strip())
    body += b
    if not ok:
      body += showUpdateStudentIdForm()
  # Students > Update: process the new name
  elif "completeStudentUpdate" in post:
    idText = post.get("idNum", [""])[0]
    b, ok = updateStudent(conn, idText, post.get("name", [""])[0])
    body += b
    if not ok:
      # show the edit form again so the user can retry
      form, found = getUpdateStudentForm(conn, idText)
      body += form
  # Students > Delete: ask for the id
  elif "delete" in post and post.get("entity", [""])[0] == "Students":
    body += showDeleteStudentIdForm()
  # Students > Delete: look up the id, show the student and ask to confirm
  elif "selectStudentDelete" in post:
    b, ok = getDeleteStudentConfirm(conn, post.get("idNum", [""])[0].strip())
    body += b
    if not ok:
      body += showDeleteStudentIdForm()
  # Students > Delete: confirmed, delete the record
  elif "confirmStudentDelete" in post:
    b, ok = deleteStudent(conn, post.get("idNum", [""])[0].strip())
    body += b
    if not ok:
      body += showDeleteStudentIdForm()
  # Students > Display: show all students
  elif "display" in post and post.get("entity", [""])[0] == "Students":
    b, ok = showAllStudents(conn)
    body += b

  ## COURSE ROUTING
  # Courses > Add: show the form
  elif "add" in post and post.get("entity", [""])[0] == "Courses":
    body += showAddCourseForm()
  # Courses > Add: process the submitted form
  elif "addCourse" in post:
    b, ok = addCourse(
      conn,
      post.get("number", [""])[0],
      post.get("title", [""])[0],
      post.get("room", [""])[0],
    )
    body += b
    if not ok:
      body += showAddCourseForm()
  # Courses > Update: ask for the course number
  elif "update" in post and post.get("entity", [""])[0] == "Courses":
    body += showUpdateCourseNumberForm()
  # Courses > Update: look up the course, show the form with current values
  elif "selectCourse" in post:
    b, ok = getUpdateCourseForm(conn, post.get("number", [""])[0])
    body += b
    if not ok:
      body += showUpdateCourseNumberForm()
  # Courses > Update: process the new values
  elif "completeCourseUpdate" in post:
    numberText = post.get("number", [""])[0]
    b, ok = updateCourse(
      conn,
      numberText,
      post.get("title", [""])[0],
      post.get("room", [""])[0],
    )
    body += b
    if not ok:
      form, found = getUpdateCourseForm(conn, numberText)
      body += form
  # Courses > Delete: ask for the course number
  elif "delete" in post and post.get("entity", [""])[0] == "Courses":
    body += showDeleteCourseNumberForm()
  # Courses > Delete: look up the course, show it and ask to confirm
  elif "selectCourseDelete" in post:
    b, ok = getDeleteCourseConfirm(conn, post.get("number", [""])[0])
    body += b
    if not ok:
      body += showDeleteCourseNumberForm()
  # Courses > Delete: confirmed, delete the record
  elif "confirmCourseDelete" in post:
    b, ok = deleteCourse(conn, post.get("number", [""])[0])
    body += b
    if not ok:
      body += showDeleteCourseNumberForm()
  # Courses > Display: show all courses
  elif "display" in post and post.get("entity", [""])[0] == "Courses":
    b, ok = showAllCourses(conn)
    body += b
  
  ##ENROLLED ROUTING
  # Enrollments > Add: show the form
  elif "add" in post and post.get("entity", [""])[0] == "Enrollments":
    body += showAddEnrollmentForm()
  # Enrollments > Add: process the submitted form
  elif "addEnrollment" in post:
    b, ok = addEnrollment(conn, post.get("student", [""])[0], post.get("course", [""])[0])
    body += b
    if not ok:
      # show the form again so the user can retry
      body += showAddEnrollmentForm()
  # Enrollments > Update: ask for the id
  elif "update" in post and post.get("entity", [""])[0] == "Enrollments":
    body += showupdateEnrollmentForm()
  # Enrollments > Update: process the submitted form
  elif "updateEnrollment" in post:
    b, ok = updateEnrollment(
      conn,
      post.get("student", [""])[0],
      post.get("currentCourse", [""])[0],
      post.get("newCourse", [""])[0],
    )
    body += b
    if not ok:
      body += showupdateEnrollmentForm()
  # Enrollments > Delete: ask for the id
  elif "delete" in post and post.get("entity", [""])[0] == "Enrollments":
    body += showDeleteEnrollmentForm()
  # Enrollments > Delete: process the submitted form
  elif "deleteEnrollment" in post:
    b, ok = deleteEnrollment(conn, post.get("student", [""])[0], post.get("course", [""])[0])
    body += b
    if not ok:
      body += showDeleteEnrollmentForm()
  # Enrollments > Display: show all enrollments
  elif "display" in post and post.get("entity", [""])[0] == "Enrollments":
    b, ok = showAllEnrollments(conn)
    body += b

  ## ROOM ROUTING
  # Rooms > Add: show the form
  elif "add" in post and post.get("entity", [""])[0] == "Rooms":
    body += showAddRoomForm()
  # Rooms > Add: process the submitted form
  elif "addRoom" in post:
    b, ok = addRoom(conn, post.get("roomNumber", [""])[0], post.get("capacity", [""])[0])
    body += b
    if not ok:
      # show the form again so the user can retry
      body += showAddRoomForm()
  # Rooms > Update: ask for the room number
  elif "update" in post and post.get("entity", [""])[0] == "Rooms":
    body += showUpdateRoomNumberForm()
  # Rooms > Update: look up the room, show the form with the current capacity
  elif "selectRoom" in post:
    b, ok = getUpdateRoomForm(conn, post.get("roomNumber", [""])[0])
    body += b
    if not ok:
      body += showUpdateRoomNumberForm()
  # Rooms > Update: process the new capacity
  elif "completeRoomUpdate" in post:
    roomNumber = post.get("roomNumber", [""])[0]
    b, ok = updateRoom(conn, roomNumber, post.get("capacity", [""])[0])
    body += b
    if not ok:
      # show the edit form again so the user can retry
      form, found = getUpdateRoomForm(conn, roomNumber)
      body += form
  # Rooms > Delete: ask for the room number
  elif "delete" in post and post.get("entity", [""])[0] == "Rooms":
    body += showDeleteRoomNumberForm()
  # Rooms > Delete: look up the room, show it and ask to confirm
  elif "selectRoomDelete" in post:
    b, ok = getDeleteRoomConfirm(conn, post.get("roomNumber", [""])[0])
    body += b
    if not ok:
      body += showDeleteRoomNumberForm()
  # Rooms > Delete: confirmed, delete the record
  elif "confirmRoomDelete" in post:
    b, ok = deleteRoom(conn, post.get("roomNumber", [""])[0])
    body += b
    if not ok:
      body += showDeleteRoomNumberForm()
  # Rooms > Display: show all rooms
  elif "display" in post and post.get("entity", [""])[0] == "Rooms":
    b, ok = showAllRooms(conn)
    body += b
  # default case: show the main menu
  else:
    body += showMainMenu()

  if conn is not None:
    conn.close()

  start_response("200 OK", [("Content-Type", "text/html")])
  return [wrapBody(body, title="University").encode("utf-8")]

  
