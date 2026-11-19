from calendar import firstweekday
from importlib import reload

from alembic.util import status
from fastapi import FastAPI,Depends,HTTPException

from chart_free_discussion_registration_cancellation_report import PublicChartFreeDiscussionRegistrationCancellationReport
from connection_database import get_db
from sqlalchemy.orm import Session, selectinload,joinedload
from datetime import datetime,timedelta,timezone

from chart_study_time_records import PublicChartStudyTimeRecord
from chart_quiz_performance_record import PublicChartQuizPerformanceRecord
from discussion_session_model import DiscussionSession
from discussion_session_topics_schema import CreateDiscussionSessionTopicALLTogether, PublicDiscussionSessionOfferedTopics
from discussion_session_registration_model import FreeDiscussionRegistration
from grammar_schema import CreateGrammar,PublicGrammar,UpdateGrammar
from grammar_model import Grammar

from exercise_schema import CreateExercise, PublicExercise, UpdateExercise
from exercise_model import Exercise
from answer_schema import CreateAnswer,PublicAnswer
from answer_model import Answer
from lesson_progress_schema import PublicLessonProgress
from section_schema import CreateSection, PublicSection, CreateSection2, UpdateSection,UpdateSection2
from section_model import Section
from question_schema import CreateQuestion,PublicQuestion,UpdateQuestion
from question_exercise_schema import PublicQuestion2
from question_model import Question
from security import pwd_context, create_access_token, get_current_admin,get_current_user
from fill_in_the_blank_answer_schema import CreateFillInTheBlankAnswer ,PublicFillInTheBlankForAdmin
from fill_in_the_blank_answer_model import FillInTheBlankAnswer
from student_discussion_vote_model import StudentDiscussionVote
from student_discussion_vote_schema import PublicStudentDiscussionVote
from user_last_activity_at import helper_function_update_user_last_activity

from user_model import User
from user_schema import CreateUser,UpdateUser,PublicUser
from course_user_schema import PublicEnrollment
from fastapi.security import OAuth2PasswordRequestForm
from course_schema import CreateCourse, UpdateCourse, PublicCourse, PublicCourseUsers
from answer_option_schema import CreateQuestionAnswerOptionALLTogether, PublicAnswerOptionForAdmin
from answer_option_model import QuestionAnswerOption
from study_session_schema import PublicStudySessionStart,PublicStudySessionEnd
from study_session_model import StudySession
from study_time_schema import PublicTotallStudyTime, PublicStudyTimeReport
from quizperformance_schema import PublicQuizPerformance
from discussion_topic_schema import CreateDiscussionTopic,PublicDiscussionTopic,UpdateDiscussionTopic
from discussion_topic_model import DiscussionTopic
from discussion_session_schema import CreateDiscussionSession,PublicDiscussionSession,UpdateDiscussionSession
from discussion_session_registration_schema import PublicDiscussionSessionRegistration



from sqlalchemy import func


from course_model import Course
from lesson_schema import CreateLesson,UpdateLesson,PublicLesson
from lesson_model import Lesson
from profile_schema import CreateProfile,PublicProfile
from profile_model import Profile
from sqlalchemy.exc import IntegrityError
from vocabulary_schema import CreateVocabulary, PublicVocabulary, UpdateVocabulary
from vocabulary_model import Vocabulary

from schedule import start_scheduler, stop_scheduler

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()

app=FastAPI(lifespan=lifespan)





@app.post("/register",response_model=PublicUser)
def register_user(user:CreateUser,db:Session=Depends(get_db)):

    current_time = datetime.now(timezone.utc)

    hashed_password = pwd_context.hash(user.password)
    db_user=User(username=user.username,email=user.email,hashed_password=hashed_password,role="student",created_at=current_time,
                 last_activity_at=None)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username==form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    if not pwd_context.verify(form_data.password,db_user.hashed_password):
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    access_token=create_access_token({"sub":form_data.username})
    return {"access_token":access_token,"token_type":"bearer"}


@app.post("/courses",response_model=PublicCourse)
def create_course(course:CreateCourse,current_user:User=Depends(get_current_admin),db:Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)
    db_course = Course(title=course.title,description=course.description,level=course.level,created_at=current_time)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@app.get("/courses",response_model=list[PublicCourse])
def read_courses(db:Session = Depends(get_db)):
    db_courses = db.query(Course).options(joinedload(Course.lessons).joinedload(Lesson.exercises).joinedload(Exercise.questions)
                                          ,joinedload(Course.lessons).joinedload(Lesson.vocabularies)).all()
    return db_courses

########temporary lazy loading endpoint
@app.get("/courses/all",response_model=list[PublicCourse])
def read_all_courses_lazily(db:Session = Depends(get_db)):
    db_courses =db.query(Course).all()
    return db_courses

######### temporarily designed to check eager loading selectinload
@app.get("/courses/allall",response_model=list[PublicCourse])
def read_all_courses_through_selectinload(db:Session = Depends(get_db)):
    db_courses =db.query(Course).options(selectinload(Course.lessons).selectinload(Lesson.exercises).selectinload(Exercise.questions)
                          ,selectinload(Course.lessons).selectinload(Lesson.vocabularies)).all()
    return db_courses



@app.get("/courses/{course_id}",response_model=PublicCourse)
def read_course(course_id:int,db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id==course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    return db_course


@app.patch("/courses/{course_id}/course",response_model=PublicCourse)
def update_course(course_id:int,course:UpdateCourse,current_user:User=Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id==course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    course_data=course.model_dump(exclude_unset=True)

    if ( "title" in course_data and course_data["title"] is None ) or ("level" in course_data and course_data["level"] is None):
        raise HTTPException(status_code=422,detail="Course title or level can not contain null value")
    for key, value in course_data.items():
        setattr(db_course,key,value)
    db.commit()
    db.refresh(db_course)
    return db_course


@app.delete("/courses/{course_id}")
def delete_course(course_id:int,current_user:User=Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id==course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    db.delete(db_course)
    db.commit()
    return {"message":"Course deleted"}

@app.post("/courses/{course_id}/lessons",response_model=PublicLesson)
def assigning_a_lesson_to_course(course_id:int,lesson:CreateLesson,current_user: User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id==course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    db_lesson=Lesson(title=lesson.title,description=lesson.description,content=lesson.content,order=lesson.order,course_id=db_course.id)

    db_existinglesson = db.query(Lesson).filter(Lesson.course_id==db_course.id,Lesson.title == db_lesson.title,
                                                Lesson.description == db_lesson.description,Lesson.content == db_lesson.content,
                                                Lesson.order == db_lesson.order).first()
    if db_existinglesson:
        raise HTTPException(status_code=400,detail="Lesson already assigned to the same course")
    db_course.lessons.append(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


@app.post("/courses/{course_id}/lessons/{lesson_id}",response_model=PublicCourse)
def removing_a_lesson_from_a_course(course_id:int,lesson_id:int,current_user:User =Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id==course_id).options(selectinload(Course.lessons).selectinload(Lesson.vocabularies)
                                         ,selectinload(Course.lessons).selectinload(Lesson.exercises).selectinload(Exercise.questions)).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    if db_lesson not in db_course.lessons:
        raise HTTPException(status_code=404,detail="Lesson not associated with course")
    db_course.lessons.remove(db_lesson)
    db.commit()
    db.refresh(db_course)
    return db_course



@app.get("/users/{user_id}/lessons",response_model=list[PublicLesson])
def user_get_lessons(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")

    db_lessons = db.query(Lesson).filter(Lesson.course.has(Course.users.any(User.id == current_user.id))).all()
    return db_lessons



@app.get("/lessons/{lesson_id}",response_model=PublicLesson)
def user_get_one_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    if db_lesson.course not in current_user.courses:
        raise HTTPException(status_code=403,detail="you are not authorized")
    return db_lesson


@app.patch("/lessons/{lesson_id}/lesson",response_model=PublicLesson)
def admin_update_lesson(lesson_id:int,lesson:UpdateLesson,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    lesson_data=lesson.model_dump(exclude_unset=True)

    if ( "title" in lesson_data and lesson_data["title"] is None ) or ( "description" in lesson_data and lesson_data["description"] is None ):
         raise HTTPException(status_code=422,detail="lesson title or description can not be null")
    if ("content" in lesson_data and lesson_data["content"] is None ) or ("order" in lesson_data and lesson_data["order"] is None):
        raise HTTPException(status_code=422,detail="lesson content or order can not be null")

    for key, value in lesson_data.items():
        setattr(db_lesson,key,value)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

@app.delete("/lessons/{lesson_id}")
def admin_delete_lesson(lesson_id:int,current_user:User=Depends(get_current_admin),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db.delete(db_lesson)
    db.commit()
    return {"message":"Lesson deleted"}

@app.delete("/lessons/{lesson_id}/{course_id}",response_model=PublicCourse)
def admin_remove_a_lesson_from_a_course(lesson_id:int,course_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db_course=db.query(Course).filter(Course.id==course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    if db_lesson not in db_course.lessons:
        raise HTTPException(status_code=404,detail="Lesson not associated with course")
    db_course.lessons.remove(db_lesson)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.post("/users/{user_id}/profile",response_model=PublicProfile)
def admin_assign_profile_to_user(user_id:int,profile:CreateProfile,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    if db_user.profile is not None:
        raise HTTPException(status_code=409,detail="User already has a profile")
    
    db_profile=Profile(first_name=profile.first_name,last_name=profile.last_name,bio=profile.bio,avatar_url=profile.avatar_url,native_language=profile.native_language,learning_level=profile.learning_level,user_id=db_user.id)
    db_user.profile=db_profile
    db.commit()
    db.refresh(db_profile)

    return db_profile

@app.get("/users",response_model=list[PublicUser])
def admin_get_all_users(current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_users=db.query(User).options(selectinload(User.profile)).all()
    return db_users


@app.get("/users/{user_id}",response_model=PublicUser)
def user_get_his_account(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    
    return db_user

@app.get("/profile/{profile_id}",response_model=PublicProfile)
def user_get_his_profile(profile_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_profile=db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404,detail="Profile not found")
    if db_profile.user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    return db_profile

# TEMPORARY LEARNING ENDPOINT
# Purpose: demonstrate IntegrityError → rollback → HTTP 409
# Remove before production
@app.post("/profile/hardcoded")
def hardcoded_profile(profile:CreateProfile,db:Session = Depends(get_db)):
    db_profile=Profile(first_name=profile.first_name,last_name=profile.last_name,bio=profile.bio,avatar_url=profile.avatar_url,
                       native_language=profile.native_language,
                       learning_level=profile.learning_level,
                       user_id=4)
    db.add(db_profile)
    try:
       db.commit()
       db.refresh(db_profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409,detail="Hardcoded profile already exists")
    return db_profile

@app.post("/lessons/{lesson_id}/vocabularies",response_model=PublicVocabulary)
def admin_assign_vocabulary_to_lesson(lesson_id:int,vocabulary:CreateVocabulary,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id==lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db_vocabulary=Vocabulary(word=vocabulary.word,definition=vocabulary.definition,
        example_sentence=vocabulary.example_sentence,part_of_speech=vocabulary.part_of_speech,
        pronunciation=vocabulary.pronunciation,translation=vocabulary.translation,difficulty=vocabulary.difficulty,
                             lesson_id=db_lesson.id)
    db_lesson.vocabularies.append(db_vocabulary)
    db.commit()
    db.refresh(db_vocabulary)
    return db_vocabulary


@app.get("/users/{user_id}/vocabularies",response_model=list[PublicVocabulary])
def user_get_all_his_vocabularies(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    db_vocabularies=(db.query(Vocabulary).filter(Vocabulary.lesson.has(Lesson.course.has(Course.users.any(User.id==current_user.id)))).all())
    return db_vocabularies

###SQLAlchemy navigates from the retrieved Lesson ORM object to its vocabularies collection.
## if that collection hasn't already been loaded, or its state has expired, the default lazy-loading behavior can trigger another SELECT to
#### retrieve the related Vocabulary records ,i didn't raise an http exception if no matching vocabularies can be found
### the endpoint returns an empty list in that case.
@app.get("/lessons/{lesson_id}/vocabularies",response_model=list[PublicVocabulary])
def user_get_vocabularies_of_a_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = (db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id == current_user.id))).first())
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found or you are not authorized")
    db_vocabularies = db_lesson.vocabularies
    return db_vocabularies



@app.get("/vocabularies/{vocabulary_id}",response_model=PublicVocabulary)
def user_get_one_specific_vocabulary(vocabulary_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_vocabulary=db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not db_vocabulary:
        raise HTTPException(status_code=404,detail="Vocabulary not found")
    db_lesson=db_vocabulary.lesson
    if db_lesson.course not in current_user.courses:
      raise HTTPException(status_code=403,detail="You are not authorized")
    return db_vocabulary

@app.patch("/vocabularies/{vocabulary_id}/vocabulary",response_model=PublicVocabulary)
def admin_update_vocabulary(vocabulary_id:int,vocabulary:UpdateVocabulary,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_vocabulary=db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not db_vocabulary:
        raise HTTPException(status_code=404,detail="Vocabulary not found")
    vocabulary_data=vocabulary.model_dump(exclude_unset=True)
    for key, value in vocabulary_data.items():
        setattr(db_vocabulary, key, value)
    db.commit()
    db.refresh(db_vocabulary)
    return db_vocabulary


@app.delete("/vocabularies/{vocabulary_id}")
def admin_delete_vocabulary(vocabulary_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_vocabulary=db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if not db_vocabulary:
        raise HTTPException(status_code=404,detail="Vocabulary not found")
    db.delete(db_vocabulary)
    db.commit()
    return {"message":"Vocabulary deleted"}


@app.delete("/vocabularies/{vocabulary_id}/{lesson_id}/orphan")
def admin_disassociate_vocabulary_from_lesson_delete_orphan(vocabulary_id:int,lesson_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):

    db_vocabulary=db.query(Vocabulary).filter(Vocabulary.id == vocabulary_id).first()
    if db_vocabulary is None:
        raise HTTPException(status_code=404,detail="Vocabulary not found")

    db_lesson=db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if db_lesson is None:
        raise HTTPException(status_code=404,detail="Lesson not found")

    if db_vocabulary.lesson_id != db_lesson.id:
        raise HTTPException(status_code=404,detail="vocabulary not associated with lesson")

    db_lesson.vocabularies.remove(db_vocabulary)
    db.commit()

    return {"message":"Vocabulary deleted"}


@app.post("/lesson/{lesson_id}/exercises",response_model=PublicExercise)
def admin_assign_exercise_to_lesson(lesson_id:int,exercise:CreateExercise,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_lesson=db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    current_time = datetime.now(timezone.utc)
    db_exercise=Exercise(title=exercise.title,instructions=exercise.instructions,
        exercise_type=exercise.exercise_type,difficulty=exercise.difficulty,order=exercise.order,lesson_id=db_lesson.id,created_at=current_time)
    db_lesson.exercises.append(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise



@app.get("/users/{user_id}/exercises",response_model=list[PublicExercise])
def user_get_all_his_exercises(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    db_exercises=(db.query(Exercise).filter(Exercise.lesson.has(Lesson.course.has(Course.users.any(User.id == current_user.id))))
                  .options(selectinload(Exercise.questions))).all()
    return db_exercises


@app.get("/lessons/{lesson_id}/exercises",response_model=list[PublicExercise])
def user_get_all_exercises_of_a_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = (db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id == current_user.id))).first())
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found or you are not authorized")
    db_exercises = db_lesson.exercises
    return db_exercises



### i keep this endpoint on purpose to remind me of joinload
@app.get("/exercises",response_model=list[PublicExercise])
def admin_read_all_exercises(current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_exercises=db.query(Exercise).options(joinedload(Exercise.questions)).all()
    return db_exercises



@app.get("/exercises/{exercise_id}",response_model=PublicExercise)
def user_get_one_specific_exercise(exercise_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_exercise=db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")
    db_lesson=db_exercise.lesson
    db_course=db_lesson.course
    if db_course not in current_user.courses:
        raise HTTPException(status_code=403,detail="You are not authorized")
    return db_exercise



@app.patch("/exercises/{exercise_id}/exercise",response_model=PublicExercise)
def admin_update_exercise(exercise_id:int,exercise:UpdateExercise,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_exercise=db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")
    exercise_data=exercise.model_dump(exclude_unset=True)
    for key,value in exercise_data.items():
        setattr(db_exercise,key,value)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

@app.delete("/exercises/{exercise_id}")
def admin_delete_exercise(exercise_id:int,current_user:User=Depends(get_current_admin),db:Session = Depends(get_db)):
    db_exercise=db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")
    db.delete(db_exercise)
    db.commit()
    return {"message":"Exercise deleted"}


@app.delete("/exercises/{exercise_id}/{lesson_id}/orphan")
def admin_disassociate_exercise_from_lesson_delete_orphan(exercise_id:int,lesson_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):

    db_exercise=db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if db_exercise is None:
        raise HTTPException(status_code=404,detail="Exercise not found")

    db_lesson=db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if db_lesson is None:
        raise HTTPException(status_code=404,detail="Lesson not found")

    if db_exercise.lesson_id != db_lesson.id:
        raise HTTPException(status_code=404,detail="Lesson not associated with this exercise")

    db_lesson.exercises.remove(db_exercise)
    db.commit()

    return {"message" : "Exercise deleted"}



@app.post("/exercises/{exercise_id}/questions",response_model=PublicQuestion)
def admin_assign_question_to_exercise(exercise_id:int,question:CreateQuestion,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_exercise=(db.query(Exercise).filter(Exercise.id == exercise_id).options(selectinload(Exercise.questions).selectinload(Question.answer_options)).first())
    if not db_exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")

    current_time = datetime.now(timezone.utc)
    db_question=Question(question_text=question.question_text,question_type=question.question_type,order=question.order,
     points=question.points,exercise_id=db_exercise.id,created_at=current_time)
    db_exercise.questions.append(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@app.get("/users/{user_id}/questions",response_model=list[PublicQuestion2])
def user_get_all_his_questions_and_exercise_of_each_question(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="You are not authorized")
    db_questions=(db.query(Question).filter(Question.exercise.has(Exercise.lesson.has(Lesson.course.has(Course.users.any(User.id==current_user.id)))))
                                                                                             .options(selectinload(Question.exercise)).all())
    return db_questions



@app.get("/questions/{question_id}",response_model=PublicQuestion)
def user_get_one_specific_question(question_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_question=db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404,detail="Question not found")
    db_exercise=db_question.exercise
    db_lesson=db_exercise.lesson
    db_course=db_lesson.course
    if db_course not in current_user.courses:
        raise HTTPException(status_code=403,detail="you are not authorized")
    return db_question


@app.patch("/{question_id}/questions",response_model=PublicQuestion)
def admin_update_question(question_id:int,question:UpdateQuestion,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_question=db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404,detail="Question not found")
    question_data=question.model_dump(exclude_unset=True)
    for key,value in question_data.items():
        setattr(db_question,key,value)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.delete("/questions/{question_id}")
def admin_delete_question(question_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_question=db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404,detail="Question not found")
    db.delete(db_question)
    db.commit()
    return {"message":"Question deleted"}


@app.delete("/exercises/{exercise_id}/{question_id}/orphann")
def admin_disassociate_question_from_exercise_delete_orphan(exercise_id:int,question_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):

    db_exercise=db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not db_exercise:
        raise HTTPException(status_code=404,detail="Exercise not found")

    db_question=db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404,detail="Question not found")

    if db_question.exercise_id != db_exercise.id:
        raise HTTPException(status_code=404,detail="Exercise not associated with question")

    db_exercise.questions.remove(db_question)
    db.commit()

    return {"message":"question deleted"}

#don't forget to implement composite uniquness between course_id and user_id inside enrollment table tomorrow
@app.post("/courses/{course_id}/users/{user_id}",response_model=PublicEnrollment)
def enroll_a_user_in_a_course(course_id:int,user_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    db_existing_user = db.query(User).filter(User.id == db_user.id,User.courses.any(Course.id == db_course.id)).first()
    if db_existing_user:
        raise HTTPException(status_code=400,detail="User already enrolled in the same course")
    db_course.users.append(db_user)
    db.commit()
    db.refresh(db_user)
    return {"user_id" : db_user.id,"course_id" :db_course.id}

#### N+1 lazy loading behavior to load the relationship attributes if not loaded or expired
@app.get("/users/{user_id}/courses",response_model=list[PublicCourse])
def read_courses_associated_with_user(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    db_courses=(db.query(Course).filter(Course.users.any(User.id == current_user.id)).all())
    return db_courses


@app.get("/courses/{course_id}/users",response_model=PublicCourseUsers)
def read_users_enrolled_in_a_course(course_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id == course_id).options(selectinload(Course.users)).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    return db_course



@app.get("/courses/{course_id}/d",response_model=PublicCourse)
def read_one_specific_course(course_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_course=db.query(Course).filter(Course.id == course_id).options(selectinload(Course.lessons).
             selectinload(Lesson.exercises).selectinload(Exercise.questions),selectinload(Course.lessons).selectinload(Lesson.vocabularies)).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    if db_course not in current_user.courses:
        raise HTTPException(status_code=403,detail="you are not authorized")
    return db_course



@ app.delete("/users/{user_id}/courses/{course_id}")
def remove_a_user_from_course(user_id:int,course_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    db_course=db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404,detail="Course not found")
    if db_course not in db_user.courses:
        raise HTTPException(status_code=404,detail="Course not associated with this user")
    db_user.courses.remove(db_course)
    db.commit()
    return {"message":"User removed from course"}



@app.patch("/users/{user_id}/user",response_model=PublicUser)
def update_user(user_id:int,user:UpdateUser,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    user_data=user.model_dump(exclude_unset=True)
    for key,value in user_data.items():
        setattr(db_user,key,value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_user=db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404,detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message":"User deleted"}


@app.get("/exercises/{exercise_id}/attempts",response_model=PublicExercise)
def user_attempts_to_see_one_exercise(exercise_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_exercise=(db.query(Exercise).filter(Exercise.id == exercise_id,Exercise.lesson.has(Lesson.course.has(Course.users.
                                                                                                            any(User.id==current_user.id)))).
                                                                                       options(selectinload(Exercise.questions).
                                                                                   selectinload(Question.answeroptions)).first())
    if not db_exercise:
        raise HTTPException(status_code=403,detail="You are not authorized")
    return db_exercise



@app.get("/questions/{question_id}/att",response_model=PublicQuestion)
def user_attempts_to_see_one_specific_question(question_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_question=(db.query(Question).filter(Question.id == question_id,Question.exercise.has(Exercise.lesson
                                                .has(Lesson.course.has(Course.users.any(User.id==current_user.id))))).
                                                         options(selectinload(Question.answer_options)).first())
    if not db_question:
        raise HTTPException(status_code=403,detail="You are not authorized")
    return db_question




@app.post("/question/{question_id}/answer",response_model=PublicAnswer)
def user_submit_answer_to_question(question_id:int,answer:CreateAnswer,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
   db_question=(db.query(Question).filter(Question.id == question_id,Question.exercise.has(Exercise.lesson.
                                            has(Lesson.course.has(Course.users.any(User.id == current_user.id))))).first())
   if not db_question:
       raise HTTPException(status_code=403,detail="you are not authorized")
   db_existing_answer=db.query(Answer).filter(Answer.question_id == db_question.id,Answer.user_id==current_user.id).first()
   if db_existing_answer:
       raise HTTPException(status_code=409,detail="You have already answered this question")

   if db_question.question_type == "multiple_choice" or db_question.question_type == "true_false":

      db_answeroption=(db.query(QuestionAnswerOption).filter(QuestionAnswerOption.question_id == db_question.id , QuestionAnswerOption.is_correct == True).first())
      if not db_answeroption:
          raise HTTPException(status_code=404,detail="Answer option not found")

      if db_answeroption.option_text == answer.selected_answer:
          correctness = True
      else:
          correctness = False

      db_answer = Answer(question_id=db_question.id, selected_answer=answer.selected_answer, user_id=current_user.id,
                         correctness=correctness, created_at=datetime.now(timezone.utc),
                         correct_answer_snapshot=db_answeroption.option_text)

   elif db_question.question_type == "fill_in_the_blank":

      db_fillintheblankanswer=db.query(FillInTheBlankAnswer).filter(FillInTheBlankAnswer.question_id==db_question.id).first()
      if not db_fillintheblankanswer:
           raise HTTPException(status_code=404,detail="fillintheblank answer not found")

      if db_fillintheblankanswer.accepted_answer == answer.selected_answer:
          correctness = True
      else:
          correctness = False

      db_answer = Answer(question_id=db_question.id, selected_answer=answer.selected_answer, user_id=current_user.id,
                      correctness=correctness,created_at=datetime.now(timezone.utc),
                      correct_answer_snapshot=db_fillintheblankanswer.accepted_answer)

   else:
       raise HTTPException(status_code=400, detail="question type does not exist")

   db.add(db_answer)

   user_last_activity_at = helper_function_update_user_last_activity(current_user)

   db.commit()
   db.refresh(db_answer)
   return {"id":db_answer.id,"question_id":db_answer.question_id,"selected_answer":db_answer.selected_answer,"user_id":db_answer.user_id,
           "correctness":correctness,"created_at":db_answer.created_at,"correct_answer_snapshot":db_answer.correct_answer_snapshot}



@app.post("/questions/{question_id}/answeroption/fillintheblank",response_model=list[PublicAnswerOptionForAdmin] | PublicFillInTheBlankForAdmin )
def admin_create_answer_to_question(question_id:int,answeroption:CreateQuestionAnswerOptionALLTogether | None = None,
                                                   fillintheblank:CreateFillInTheBlankAnswer | None = None,
                                                    current_user:User =Depends(get_current_admin),db:Session = Depends(get_db)):
    db_question=db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404,detail="Question not found" )

    if answeroption is None and fillintheblank is None:
        raise HTTPException(status_code=400,detail="you should provide an answer body")
    if answeroption is not None and fillintheblank is not None:
        raise HTTPException(status_code=400,detail="Please provide only one answer body.")

    if db_question.question_type == "multiple_choice" or db_question.question_type == "true_false":
        if answeroption is None:
            raise HTTPException(status_code=400,detail="you should provide multiplechoice or truefalse answer")

        answeroptions=[]

        for i in answeroption.options:
               db_answeroption=QuestionAnswerOption(option_text=i.option_text,is_correct=i.is_correct,question_id=db_question.id)
               db.add(db_answeroption)
               answeroptions.append(db_answeroption)

        db.commit()
        for j in answeroptions:
          db.refresh(j)
        return answeroptions

    else:
        if fillintheblank is None:
            raise HTTPException(status_code=400,detail="you should provide fillintheblank answer")
        db_fillintheblankanswer = FillInTheBlankAnswer(accepted_answer=fillintheblank.accepted_answer,question_id=db_question.id)
        db.add(db_fillintheblankanswer)
        db.commit()
        db.refresh(db_fillintheblankanswer)
        return db_fillintheblankanswer



@app.post("/lessons/{lesson_id}/sections/startstudysession",response_model=PublicStudySessionStart)
def user_start_a_study_session(lesson_id:int,section:CreateSection2,current_user:User =Depends(get_current_user),db:Session = Depends(get_db)):

    current_time = datetime.now(timezone.utc)

    db_lesson=(db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id==current_user.id))).first())

    if not db_lesson:
        raise HTTPException(status_code=404,detail="you are not authorized")


    if section.section_id is not None:

     db_section = db.query(Section).filter(Section.id == section.section_id,Section.lesson_id == db_lesson.id).first()

     if not db_section:
          raise HTTPException(status_code=404,detail="section not found or section not associated with this lesson")

    db_existing_study_session = db.query(StudySession).filter(StudySession.user_id == current_user.id, StudySession.status == "active").first()
    if not db_existing_study_session:

        db_newstudysession = StudySession(lesson_id=db_lesson.id, user_id=current_user.id, started_at=current_time,ended_at=None,duration_minutes=None,
                                          last_activity_at=current_time,status="active",section_id=section.section_id)
        db.add(db_newstudysession)

    elif  ( db_existing_study_session.section_id == section.section_id and db_existing_study_session.lesson_id == db_lesson.id
                         and current_time-timedelta(minutes=2) <= db_existing_study_session.last_activity_at <= current_time):

        raise HTTPException(status_code=409,detail="you already have an active study session for both same lesson and section needs to be ended")

    elif ((  ( db_existing_study_session.section_id != section.section_id and db_existing_study_session.lesson_id == db_lesson.id )
           or db_existing_study_session.lesson_id != db_lesson.id ) and
              (current_time - timedelta(minutes=2)  <= db_existing_study_session.last_activity_at <= current_time )):

               db_existing_study_session.status = "completed"
               db_existing_study_session.ended_at = current_time
               db_existing_study_session.last_activity_at = current_time

               duration_minutes = (db_existing_study_session.ended_at - db_existing_study_session.started_at)

               db_existing_study_session.duration_minutes = (duration_minutes.total_seconds() / 60)

               db_newstudysession = StudySession(lesson_id=db_lesson.id, user_id=current_user.id, started_at=current_time,
                                          ended_at=None, duration_minutes=None, last_activity_at=current_time,
                                          status="active",section_id=section.section_id)
               db.add(db_newstudysession)

    elif  db_existing_study_session.last_activity_at < current_time - timedelta(minutes=2):

                db_existing_study_session.status = "expired"

                db_newstudysession = StudySession(lesson_id=db_lesson.id,user_id=current_user.id,started_at=current_time,
                                                ended_at=None,duration_minutes=None,last_activity_at=current_time,
                                                status="active",section_id=section.section_id)
                db.add(db_newstudysession)

    else:
        raise HTTPException(status_code=409,detail="Unexpected study session activity timestamp")

    user_last_activity_at = helper_function_update_user_last_activity(current_user)

    db.commit()
    db.refresh(db_newstudysession)
    return db_newstudysession


@app.post("/studysessions/{study_session_id}/finishstudysession",response_model=PublicStudySessionEnd)
def user_finish_a_study_session(study_session_id:int,current_user:User =Depends(get_current_user),db:Session = Depends(get_db)):

    current_time = datetime.now(timezone.utc)

    db_study_session=(db.query(StudySession).filter(StudySession.id == study_session_id,StudySession.user_id==current_user.id).first())
    if not db_study_session:
        raise HTTPException(status_code=404,detail="you are not authorized")

    if  db_study_session.status != "active":
           raise HTTPException(status_code=400,detail="study session already ended")

    elif db_study_session.last_activity_at < current_time - timedelta(minutes=2) :
         db_study_session.status = "expired"

    elif current_time - timedelta(minutes=2) <= db_study_session.last_activity_at <= current_time:
          db_study_session.status = "completed"
          db_study_session.last_activity_at = current_time
          db_study_session.ended_at = current_time
          duration_minutes = ( db_study_session.ended_at - db_study_session.started_at )
          db_study_session.duration_minutes = duration_minutes.total_seconds() / 60


    user_last_activity_at = helper_function_update_user_last_activity(current_user)

    db.commit()
    db.refresh(db_study_session)
    return db_study_session


########calculation performed by database at database level using fun.sum
@app.get("/studytime",response_model=PublicTotallStudyTime)
def user_get_his_total_study_time(current_user:User =Depends(get_current_user),db:Session = Depends(get_db)):
    total_study_time=(db.query(func.sum(StudySession.duration_minutes)).filter(StudySession.user_id==current_user.id,
                                                                               StudySession.status == "completed",
                                                                               StudySession.ended_at != None).scalar())
    if total_study_time is None:
        raise HTTPException(status_code=404,detail="No study sessions found")

    hours=int(total_study_time // 60)
    minutes=int(total_study_time % 60)

    return { "total_study_time" :  f"{hours} h  { minutes} min"  }


#######calculation performed by python at the application level
@app.get("/studytime/pp")
def user_get_his_total_study_time(current_user:User =Depends(get_current_user),db:Session = Depends(get_db)):
    db_studeysessions=db.query(StudySession).filter(StudySession.user_id==current_user.id).all()
    if not db_studeysessions:
        raise HTTPException(status_code=404,detail="No study sessions found")

    total_study_time = 0

    for i in db_studeysessions:
        each_session_study_time=i.duration_minutes
        total_study_time = each_session_study_time + total_study_time

    hours=int(total_study_time // 60)
    minutes=int(total_study_time % 60)

    return { "total_study_time" : f"{hours} h  { minutes} min"}

###i didn't initialized accmulators below the query cause i want
###the loop to be executed regardless of which branch has been executed
@app.get("/reports/studytimereports",response_model=PublicStudyTimeReport)
def user_get_study_sessions_time_reports(section_name:str | None = None,current_user:User =Depends(get_current_user),db:Session = Depends(get_db)):

    today = datetime.now(timezone.utc)
    beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    beginning_of_tomorrow = beginning_of_today + timedelta(days=1)

    if section_name is None:

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_tomorrow,
                                                                            StudySession.ended_at > beginning_of_today,
                                                                            StudySession.user_id == current_user.id,
                                                                            StudySession.section_id == None,
                                                                            StudySession.ended_at != None,
                                                                            StudySession.status == "completed").all()
    else:

        db_study_sessions = (db.query(StudySession).filter(StudySession.started_at < beginning_of_tomorrow,
                                                          StudySession.ended_at > beginning_of_today,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.ended_at != None,
                                                          StudySession.status == "completed",
                                                          StudySession.section.has(Section.name == section_name)).all())

    today_total_study_time_duration_minutes = 0
    yesterday_total_study_time_duration_minutes = 0
    tomorrow_total_study_time_duration_minutes = 0

    for i in db_study_sessions:
            if i.started_at >= beginning_of_today and i.ended_at <= beginning_of_tomorrow:
               today_duration_minutes = ( i.ended_at - i.started_at ).total_seconds() / 60
               today_total_study_time_duration_minutes = today_duration_minutes + today_total_study_time_duration_minutes

            elif i.started_at < beginning_of_today and i.ended_at <= beginning_of_tomorrow:
                yesterday_duration_minutes = ( beginning_of_today - i.started_at ).total_seconds() / 60
                yesterday_total_study_time_duration_minutes = yesterday_duration_minutes + yesterday_total_study_time_duration_minutes
                today_duration_minutes = ( i.ended_at - beginning_of_today ).total_seconds() / 60
                today_total_study_time_duration_minutes = today_duration_minutes + today_total_study_time_duration_minutes

            elif i.started_at >= beginning_of_today and i.ended_at > beginning_of_tomorrow:
                tomorrow_duration_minutes = ( i.ended_at - beginning_of_tomorrow ).total_seconds() / 60
                tomorrow_total_study_time_duration_minutes = tomorrow_duration_minutes + tomorrow_total_study_time_duration_minutes
                today_duration_minutes = ( beginning_of_tomorrow - i.started_at ).total_seconds() / 60
                today_total_study_time_duration_minutes = today_duration_minutes + today_total_study_time_duration_minutes

            elif i.started_at < beginning_of_today and i.ended_at > beginning_of_tomorrow:
                yesterday_duration_minutes = ( beginning_of_today - i.started_at ).total_seconds() / 60
                yesterday_total_study_time_duration_minutes = yesterday_duration_minutes + yesterday_total_study_time_duration_minutes
                today_duration_minutes = ( beginning_of_tomorrow - beginning_of_today ).total_seconds() / 60
                today_total_study_time_duration_minutes = today_duration_minutes + today_total_study_time_duration_minutes
                tomorrow_duration_minutes = ( i.ended_at - beginning_of_tomorrow ).total_seconds() / 60
                tomorrow_total_study_time_duration_minutes = tomorrow_duration_minutes + tomorrow_total_study_time_duration_minutes


    today_total_study_time =  today_total_study_time_duration_minutes


    if today_total_study_time_duration_minutes == 0:
            daily_hours = 0
            daily_minutes = 0
    else:
            daily_hours = int(today_total_study_time // 60)
            daily_minutes = int(today_total_study_time % 60)



    beginning_of_this_week = beginning_of_today - timedelta(days=beginning_of_today.weekday())
    beginning_of_next_week = beginning_of_this_week + timedelta(days=7)

    if section_name is None:

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_week,
                                                                             StudySession.ended_at > beginning_of_this_week,
                                                                             StudySession.user_id == current_user.id,
                                                                             StudySession.section_id == None,
                                                                             StudySession.ended_at != None,
                                                                             StudySession.status == "completed").all()
    elif section_name is not None:

        db_study_sessions = (db.query(StudySession).filter(StudySession.started_at < beginning_of_next_week,
                                                          StudySession.ended_at > beginning_of_this_week,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.ended_at != None,
                                                          StudySession.status == "completed",
                                                          StudySession.section.has(Section.name == section_name)).all())

    this_week_duration_minutes = 0
    last_week_duration_minutes = 0
    next_week_duration_minutes = 0

    for j in db_study_sessions:
            if j.started_at >= beginning_of_this_week and j.ended_at <= beginning_of_next_week:
                duration_minutes = ( j.ended_at - j.started_at ).total_seconds() / 60
                this_week_duration_minutes = duration_minutes + this_week_duration_minutes
            elif j.started_at < beginning_of_this_week and j.ended_at <= beginning_of_next_week:
                duration_minutes = ( beginning_of_this_week - j.started_at ).total_seconds() / 60
                last_week_duration_minutes =  duration_minutes + last_week_duration_minutes
                duration_minutes = ( j.ended_at - beginning_of_this_week ).total_seconds() / 60
                this_week_duration_minutes = duration_minutes + this_week_duration_minutes
            elif j.started_at >= beginning_of_this_week and j.ended_at > beginning_of_next_week:
                duration_minutes = ( j.ended_at - beginning_of_next_week ).total_seconds() / 60
                next_week_duration_minutes = duration_minutes + next_week_duration_minutes
                duration_minutes = ( beginning_of_next_week - j.started_at ).total_seconds() / 60
                this_week_duration_minutes = duration_minutes + this_week_duration_minutes
            elif j.started_at < beginning_of_this_week and j.ended_at > beginning_of_next_week:
                duration_minutes = ( beginning_of_this_week - j.started_at ).total_seconds() / 60
                last_week_duration_minutes = duration_minutes + last_week_duration_minutes
                duration_minutes = ( beginning_of_next_week - beginning_of_this_week ).total_seconds() / 60
                this_week_duration_minutes = duration_minutes + this_week_duration_minutes
                duration_minutes = ( j.ended_at - beginning_of_next_week ).total_seconds() / 60
                next_week_duration_minutes = duration_minutes + next_week_duration_minutes

    this_week_total_study_time = this_week_duration_minutes

    if this_week_total_study_time == 0:
             weekly_hours = 0
             weekly_minutes = 0
    else:
             weekly_hours = int( this_week_total_study_time // 60 )
             weekly_minutes = int( this_week_total_study_time % 60 )




    today_day_of_month = beginning_of_today.day
    beginning_of_this_month = beginning_of_today - timedelta( days = today_day_of_month-1 )

    if beginning_of_this_month.month == 12:
        beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year + 1,month= 1,
                                                                  day=1,hour=0,minute=0,second=0,microsecond=0)
    else:

        beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year,month=beginning_of_this_month.month +1,
                                                                  day=1,hour=0, minute=0, second=0, microsecond=0)

    if section_name is None:

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_month,
                                                                 StudySession.ended_at > beginning_of_this_month,
                                                                 StudySession.user_id == current_user.id,
                                                                 StudySession.section_id == None,
                                                                 StudySession.ended_at != None,
                                                                 StudySession.status == "completed").all()

    elif section_name is not None:

        db_study_sessions = (db.query(StudySession).filter(StudySession.started_at < beginning_of_next_month,
                                                          StudySession.ended_at > beginning_of_this_month,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.ended_at != None,
                                                          StudySession.status == "completed",
                                                          StudySession.section.has(Section.name == section_name)).all())


    this_month_study_time = 0
    last_month_study_time = 0
    next_month_study_time = 0

    for k in db_study_sessions:
             if k.started_at >= beginning_of_this_month and k.ended_at <= beginning_of_next_month:
               duration_minutes = ( k.ended_at - k.started_at ).total_seconds() / 60
               this_month_study_time = duration_minutes + this_month_study_time

             elif k.started_at < beginning_of_this_month and k.ended_at <= beginning_of_next_month:
               duration_minutes = ( beginning_of_this_month - k.started_at ).total_seconds() / 60
               last_month_study_time = duration_minutes + last_month_study_time
               duration_minutes = ( k.ended_at - beginning_of_this_month ).total_seconds() / 60
               this_month_study_time = duration_minutes + this_month_study_time

             elif k.started_at >= beginning_of_this_month and k.ended_at > beginning_of_next_month:
               duration_minutes = ( k.ended_at - beginning_of_next_month ).total_seconds() / 60
               next_month_study_time = duration_minutes + next_month_study_time
               duration_minutes = ( beginning_of_next_month - k.started_at ).total_seconds() / 60
               this_month_study_time = duration_minutes + this_month_study_time

             elif k.started_at < beginning_of_this_month and k.ended_at > beginning_of_next_month:
               duration_minutes = ( beginning_of_this_month - k.started_at ).total_seconds() / 60
               last_month_study_time = duration_minutes + last_month_study_time
               duration_minutes = ( beginning_of_next_month - beginning_of_this_month ).total_seconds() / 60
               this_month_study_time = duration_minutes + this_month_study_time
               duration_minutes = ( k.ended_at - beginning_of_next_month ).total_seconds() / 60
               next_month_study_time = duration_minutes + next_month_study_time

    this_month_total_study_time = this_month_study_time

    if this_month_total_study_time == 0:
          monthly_hours = 0
          monthly_minutes = 0
    else:
          monthly_hours = int( this_month_total_study_time // 60 )
          monthly_minutes = int( this_month_total_study_time % 60 )



    if 7 <= beginning_of_this_month.month <= 12:

        beginning_of_six_month_ago = beginning_of_this_month.replace(year=beginning_of_this_month.year,
                                                                     month=beginning_of_this_month.month - 6,
                                                                     day=1,hour=0,minute=0,
                                                                     second=0,microsecond=0)
    else:
        beginning_of_six_month_ago = beginning_of_this_month.replace(year=beginning_of_this_month.year - 1,
                                                                     month=beginning_of_this_month.month + 6,
                                                                     day=1,hour=0,minute=0,
                                                                     second=0,microsecond=0)

    if section_name is None:

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_this_month,
                                                                   StudySession.ended_at > beginning_of_six_month_ago,
                                                                   StudySession.user_id == current_user.id,
                                                                   StudySession.section_id == None,
                                                                   StudySession.ended_at != None,
                                                                   StudySession.status == "completed").all()


    elif section_name is not None:

        db_study_sessions = (db.query(StudySession).filter(StudySession.started_at < beginning_of_this_month,
                                                                   StudySession.ended_at > beginning_of_six_month_ago,
                                                                   StudySession.user_id == current_user.id,
                                                                   StudySession.ended_at != None,
                                                                   StudySession.status == "completed",
                                                                   StudySession.section.has(Section.name == section_name)).all())


    six_month_study_time = 0
    before_six_month_study_time = 0
    after_six_month_study_time = 0

    for r in db_study_sessions:
            if r.started_at >= beginning_of_six_month_ago and r.ended_at <= beginning_of_this_month:
              duration_minutes = ( r.ended_at - r.started_at ).total_seconds() / 60
              six_month_study_time = duration_minutes + six_month_study_time

            elif r.started_at < beginning_of_six_month_ago and r.ended_at <= beginning_of_this_month:
               duration_minutes =( beginning_of_six_month_ago - r.started_at ).total_seconds() / 60
               before_six_month_study_time = duration_minutes + before_six_month_study_time
               duration_minutes = ( r.ended_at - beginning_of_six_month_ago).total_seconds() / 60
               six_month_study_time = duration_minutes + six_month_study_time


            elif r.started_at >= beginning_of_six_month_ago and r.ended_at > beginning_of_this_month:
               duration_minutes = ( r.ended_at - beginning_of_this_month ).total_seconds() / 60
               after_six_month_study_time = duration_minutes + after_six_month_study_time
               duration_minutes = ( beginning_of_this_month - r.started_at ).total_seconds() / 60
               six_month_study_time = duration_minutes + six_month_study_time

            elif r.started_at < beginning_of_six_month_ago and r.ended_at > beginning_of_this_month:
               duration_minutes = ( beginning_of_six_month_ago - r.started_at ).total_seconds() / 60
               before_six_month_study_time = duration_minutes + before_six_month_study_time
               duration_minutes = ( beginning_of_this_month - beginning_of_six_month_ago ).total_seconds() / 60
               six_month_study_time = duration_minutes + six_month_study_time
               duration_minutes = ( r.ended_at - beginning_of_this_month ).total_seconds() / 60
               after_six_month_study_time = duration_minutes + after_six_month_study_time


    six_month_total_study_time = six_month_study_time

    if six_month_total_study_time == 0:
            six_month_hours = 0
            six_month_minutes = 0
    else:
            six_month_hours = int(six_month_total_study_time // 60 )
            six_month_minutes = int(six_month_total_study_time % 60 )



    beginning_of_this_year = beginning_of_today.replace(year=beginning_of_today.year,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
    beginning_of_next_year = beginning_of_this_year.replace(year=beginning_of_this_year.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)

    if section_name is None:

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_year,
                                                                       StudySession.ended_at > beginning_of_this_year,
                                                                       StudySession.user_id==current_user.id,
                                                                       StudySession.section_id == None,
                                                                       StudySession.ended_at != None,
                                                                       StudySession.status == "completed").all()

    elif section_name is not None:

        db_study_sessions = (db.query(StudySession).filter(StudySession.started_at < beginning_of_next_year,
                                                          StudySession.ended_at > beginning_of_this_year,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.ended_at != None,
                                                          StudySession.status == "completed",
                                                          StudySession.section.has(Section.name == section_name)).all())


    this_year_study_time = 0
    next_year_study_time = 0
    last_year_study_time = 0

    for e in db_study_sessions:
             if  e.started_at >= beginning_of_this_year and e.ended_at <= beginning_of_next_year:
                  duration_minutes = ( e.ended_at - e.started_at ).total_seconds() / 60
                  this_year_study_time = duration_minutes + this_year_study_time

             elif e.started_at >= beginning_of_this_year and e.ended_at > beginning_of_next_year:
                  duration_minutes = ( e.ended_at - beginning_of_next_year).total_seconds() / 60
                  next_year_study_time = duration_minutes + next_year_study_time
                  duration_minutes = ( beginning_of_next_year - e.started_at ).total_seconds() / 60
                  this_year_study_time = duration_minutes + this_year_study_time

             elif e.started_at < beginning_of_this_year and e.ended_at <= beginning_of_next_year:
                  duration_minutes = ( beginning_of_this_year - e.started_at ).total_seconds() / 60
                  last_year_study_time = duration_minutes + last_year_study_time
                  duration_minutes = ( e.ended_at - beginning_of_this_year ).total_seconds() / 60
                  this_year_study_time = duration_minutes + this_year_study_time

             elif e.started_at < beginning_of_this_year and e.ended_at > beginning_of_next_year:
                  duration_minutes = ( beginning_of_this_year - e.started_at ).total_seconds() / 60
                  last_year_study_time = duration_minutes + last_year_study_time
                  duration_minutes = ( beginning_of_next_year - beginning_of_this_year ).total_seconds() / 60
                  this_year_study_time = duration_minutes + this_year_study_time
                  duration_minutes = ( e.ended_at - beginning_of_next_year ).total_seconds() / 60
                  next_year_study_time = duration_minutes + next_year_study_time

    this_year_total_study_time = this_year_study_time
    if this_year_total_study_time == 0:
                this_year_hours = 0
                this_year_minutes = 0
    else:
                this_year_hours = int(this_year_total_study_time // 60 )
                this_year_minutes = int(this_year_total_study_time % 60 )




    return {"daily_study_time_report" : f"{daily_hours} h {daily_minutes} min","weekly_study_time_report" : f"{weekly_hours} h {weekly_minutes} min",
            "monthly_study_time_report" : f"{monthly_hours} h {monthly_minutes} min","six_month_study_time_report" : f"{six_month_hours} h {six_month_minutes} min",
            "yearly_study_time_report" : f"{this_year_hours} h {this_year_minutes} min"}

#helper function for the following endpoint to avoid repeating the same logic for each question type
#the only parameter that changes is the question_type in helper function
#instead of writing same four quesries for each question type,we write it once in the helper
#and call that helper with different arguments
#helper doesn't reduce the number of SQL statements,it runs four queries per call,so for three question types sqlalchemy sends tweleve queries

def each_question_type_counting(question_type:str,exercise_id:int,user_id:int,db:Session):

    number_of_each_question_type = db.query(Question).filter(Question.exercise_id == exercise_id,
                                                                 Question.question_type == question_type).count()

    number_of_each_question_type_answered_by_user = db.query(Question).filter(Question.exercise_id == exercise_id,
                                                                                      Question.question_type == question_type,
                                                                                      Question.answers.any(Answer.user_id == user_id)).count()

    number_of_each_question_type_answered_correctly = db.query(Question).filter(Question.exercise_id == exercise_id,
                                                                 Question.question_type == question_type,
                                                                 Question.answers.any(
                                                                     (Answer.user_id == user_id) &
                                                                     (Answer.correctness == True))).count()

    number_of_each_question_type_answered_incorrectly = db.query(Question).filter(Question.exercise_id == exercise_id,
                                                                                      Question.question_type == question_type,
                                                                                      Question.answers.any(
                                                                                    (Answer.user_id == user_id) &
                                                                                    (Answer.correctness == False))).count()

    return {"number_of_each_question_type": number_of_each_question_type,
            "number_of_each_question_type_answered_correctly" :number_of_each_question_type_answered_correctly,
            "number_of_each_question_type_answered_incorrectly" :number_of_each_question_type_answered_incorrectly,
            "number_of_each_question_type_answered_by_user" :number_of_each_question_type_answered_by_user}



@app.get("/exercises/{exercise_id}/quizperformance",response_model=PublicQuizPerformance)
def user_get_quiz_performance(exercise_id:int,current_user:User = Depends(get_current_user),db :Session = Depends(get_db)):

    db_exercise = db.query(Exercise).filter(Exercise.id == exercise_id,Exercise.lesson.has(Lesson.course
                                    .has(Course.users.any(User.id == current_user.id)))).first()
    if not db_exercise:
        raise HTTPException(status_code=404,detail="you are not authorized")

    number_of_questions = db.query(Question).filter(Question.exercise_id == db_exercise.id).count()

    number_of_questions_answered_by_user = db.query(Question).filter(Question.exercise_id == db_exercise.id,
                                             Question.answers.any(
                                             Answer.user_id == current_user.id)).count()

    number_of_correct_answers_by_user = db.query(Question).filter(Question.exercise_id == db_exercise.id,
                                                                     Question.answers.any(
                                                                         (Answer.user_id == current_user.id) &
                                                                         (Answer.correctness == True))).count()

    number_of_incorrect_answers_by_user = db.query(Question).filter(Question.exercise_id == db_exercise.id,
                                                                    Question.answers.any(
                                                                    (Answer.user_id == current_user.id) &
                                                                    (Answer.correctness == False))).count()

    number_of_unanswered_questions = (number_of_questions - number_of_questions_answered_by_user)

    if number_of_questions_answered_by_user == 0:
        percentage_of_correct_answers = None

    else:
        percentage_of_correct_answers = ( (number_of_correct_answers_by_user /  number_of_questions_answered_by_user) * 100 )



    returned_dictionary1 = each_question_type_counting(exercise_id = db_exercise.id , question_type = "multiple_choice", user_id = current_user.id,db=db)
    returned_dictionary2 = each_question_type_counting(exercise_id = db_exercise.id , question_type = "fill_in_the_blank", user_id = current_user.id,db=db)
    returned_dictionary3 = each_question_type_counting(exercise_id = db_exercise.id , question_type = "true_false", user_id = current_user.id,db=db)



    return {"number_of_questions" : number_of_questions,"number_of_questions_answered_by_user" : number_of_questions_answered_by_user,
            "number_of_correct_answers_by_user" :  number_of_correct_answers_by_user ,"number_of_incorrect_answers_by_user" : number_of_incorrect_answers_by_user ,
            "number_of_unanswered_questions" : number_of_unanswered_questions,"percentage_of_correct_answers" : percentage_of_correct_answers,
            "number_of_multiple_choice_questions" : returned_dictionary1["number_of_each_question_type"],
            "number_of_multiple_choice_questions_answered_by_user" :returned_dictionary1["number_of_each_question_type_answered_by_user"],
            "number_of_multiple_choice_questions_answered_by_user_correctly" :returned_dictionary1["number_of_each_question_type_answered_correctly"],
            "number_of_multiple_choice_questions_answered_by_user_incorrectly": returned_dictionary1["number_of_each_question_type_answered_incorrectly"],
            "number_of_fill_in_the_blank_questions": returned_dictionary2["number_of_each_question_type"],
            "number_of_fill_in_the_blank_questions_answered_by_user" :returned_dictionary2["number_of_each_question_type_answered_by_user"],
            "number_of_fill_in_the_blank_questions_answered_by_user_correctly" :returned_dictionary2["number_of_each_question_type_answered_correctly"],
            "number_of_fill_in_the_blank_questions_answered_by_user_incorrectly": returned_dictionary2["number_of_each_question_type_answered_incorrectly"],
            "number_of_true_false_questions": returned_dictionary3["number_of_each_question_type"],
            "number_of_true_false_questions_answered_by_user": returned_dictionary3["number_of_each_question_type_answered_by_user"],
            "number_of_true_false_questions_answered_by_user_correctly": returned_dictionary3["number_of_each_question_type_answered_correctly"],
            "number_of_true_false_questions_answered_by_user_incorrectly": returned_dictionary3["number_of_each_question_type_answered_incorrectly"] }





@app.post("/lessons/{lesson_id}/sections",response_model=PublicSection)
def assign_section_to_lesson(lesson_id:int,section:CreateSection,current_user:User = Depends(get_current_admin),
                             db: Session = Depends(get_db)):
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db_section = Section(name=section.name)
    db_lesson.sections.append(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section
#since first query already establishes section exists and checks it's association with lesson,so second query is redundant
#i keep second query cause it may be easier to follow while learning
@app.post("/lesson/{lesson_id}/{section_id}/orphan",response_model=PublicLesson)
def remove_section_from_lesson(lesson_id:int,section_id:int,current_user:User = Depends(get_current_admin),
                               db: Session = Depends(get_db)):
    db_lesson = (db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.sections.any(Section.id == section_id)).
         options(selectinload(Lesson.vocabularies),selectinload(Lesson.exercises).selectinload(Exercise.questions).selectinload(Question.answer_options),
                 selectinload(Lesson.sections)).first())
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found or section not associated with lesson")
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404,detail="Section not found")

    db_lesson.sections.remove(db_section)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

# Version 2: Retrieve and authorize the parent resource (Lesson) first,
# then access its relationship attribute: db_lesson.sections.
@app.get("/lessons/{lesson_id}/assignedsections",response_model=list[PublicSection])
def user_get_sections_assigned_to_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has
                                                     (Course.users.any(User.id == current_user.id))).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db_sections = db_lesson.sections
    return db_sections


# Version 1: Query directly from the requested resource table (Section).
# Filter the Sections and verify authorization through nested relationships.
@app.get("/sections/{lesson_id}",response_model=list[PublicSection])
def user_get_sections_assigned_to_a_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id == current_user.id))).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found or you are not authorized")

    db_sections = db.query(Section).filter(Section.lesson_id == lesson_id,Section.lesson.has(Lesson.course.has
                                                                          (Course.users.any(User.id == current_user.id)))).all()
    return db_sections


@app.patch("/sections/{section_id}/section",response_model=PublicSection)
def update_section_while_keeping_it_assigned_to_same_lesson(section_id:int,section:UpdateSection,current_user = Depends(get_current_admin),
                                                            db:Session = Depends(get_db)):
    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404,detail="Section not found")
    section_data = section.model_dump(exclude_unset=True)
    for key,value in section_data.items():
        setattr(db_section,key,value)
    db.commit()
    db.refresh(db_section)
    return db_section



#composite uniquness that lesson_id and name form together
#to avoid uniquness constaraint violation sqlalchemy check whether there is an existing section or not
#if i have implemented update inside else statement it would have never been executed
@app.patch("/sections/{section_id}/sectionlesson")
def update_section_while_removing_its_assigned_lesson(section_id:int,section:UpdateSection2,current_user:User = Depends(get_current_admin),
                                                      db:Session = Depends(get_db)):

    db_section = db.query(Section).filter(Section.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404,detail="Section not found")

    db_lesson = db.query(Lesson).filter(Lesson.id == section.lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")

    if section.name !=None:
        db_existing_section = db.query(Section).filter(Section.name == section.name,Section.lesson_id == section.lesson_id,
                                                       Section.id != db_section.id).first()
        if db_existing_section:
          raise HTTPException(status_code=409,detail="section already exists")

    elif section.name ==None:
        db_existing_section = db.query(Section).filter(Section.lesson_id == section.lesson_id,Section.name ==db_section.name,
                                                       Section.id != db_section.id).first()
        if db_existing_section:
           raise HTTPException(status_code=409,detail="section already exists")

    section_data = section.model_dump(exclude_unset=True)
    for key,value in section_data.items():
          setattr(db_section,key,value)
    db.commit()
    db.refresh(db_section)
    return db_section

@app.post("/lessons/{lesson_id}/grammars",response_model=PublicGrammar)
def assign_grammar_to_lesson(lesson_id:int,grammar:CreateGrammar,current_user:User = Depends(get_current_admin),
                             db:Session = Depends(get_db)):
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not db_lesson:
        raise HTTPException(status_code=404,detail="Lesson not found")
    db_grammar = Grammar(title=grammar.title,explanation=grammar.explanation,examples=grammar.examples,order=grammar.order)
    db_lesson.grammars.append(db_grammar)
    db.commit()
    db.refresh(db_grammar)
    return db_grammar

@app.get("/grammars/{grammar_id}",response_model=PublicGrammar)
def user_get_one_grammar(grammar_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_grammar = db.query(Grammar).filter(Grammar.id == grammar_id).first()
    if not db_grammar:
        raise HTTPException(status_code=404,detail="Grammar not found")

    db_grammar_associated_with_user_indirectly = (db.query(Grammar).filter(Grammar.id == db_grammar.id,
                                                     Grammar.lesson.has(Lesson.course.has(Course.users.any(User.id == current_user.id)))).first())
    if not db_grammar_associated_with_user_indirectly:
        raise HTTPException(status_code=403,detail="you are not authorized")
    return db_grammar


@app.get("/users/{user_id}/grammars",response_model=list[PublicGrammar])
def user_get_all_his_grammars(user_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403,detail="you are not authorized")
    db_grammars = (db.query(Grammar).filter(Grammar.lesson.has(Lesson.course.has(Course.users.any(User.id == current_user.id)))).all())
    return db_grammars


@app.get("/lessons/{lesson_id}/grammars",response_model=list[PublicGrammar])
def user_get_all_grammars_of_a_lesson(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = (db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id == current_user.id))).first())
    if not db_lesson:
        raise HTTPException(status_code=404,detail="lesson not found or you are not authorized")
    db_grammars = db.query(Grammar).filter(Grammar.lesson_id == db_lesson.id).all()

    return db_grammars

### With if and elif, Python checks the second condition only if the first condition is false.
#### With two separate if statements, Python checks both conditions independently.
@app.patch("/grammars/{grammar_id}/grammar",response_model=PublicGrammar)
def admin_update_grammar(grammar_id:int,grammar:UpdateGrammar,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_grammar = db.query(Grammar).filter(Grammar.id == grammar_id).first()
    if not db_grammar:
        raise HTTPException(status_code=404,detail="grammar not found")
    grammar_data = grammar.model_dump(exclude_unset=True)
    if "title" in grammar_data and grammar_data["title"] is None:
        raise HTTPException(status_code=400,detail="title can not be none")
    if "explanation" in grammar_data and grammar_data["explanation"] is None:
        raise HTTPException(status_code=400,detail="explanation can not be none")

    for key,value in grammar_data.items():
        setattr(db_grammar,key,value)
    db.commit()
    db.refresh(db_grammar)
    return db_grammar


@app.delete("/grammars/{grammar_id}")
def admin_delete_a_grammar(grammar_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):
    db_grammar = db.query(Grammar).filter(Grammar.id == grammar_id).first()
    if db_grammar is None:
        raise HTTPException(status_code=404,detail="grammar not found")
    db.delete(db_grammar)
    db.commit()
    return {"message" : "grammar deleted"}



@app.post("/grammars/{grammar_id}/{lesson_id}/orphan")
def admin_disassociates_a_grammar_from_a_lesson(grammar_id:int,lesson_id:int,current_user:User = Depends(get_current_admin),db:Session = Depends(get_db)):

    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if db_lesson is None:
        raise HTTPException(status_code=404,detail="lesson not found")

    db_grammar = db.query(Grammar).filter(Grammar.id == grammar_id).first()
    if db_grammar is None:
        raise HTTPException(status_code=404,detail="grammar not found")

    if db_grammar.lesson_id != db_lesson.id:
        raise HTTPException(status_code=404,detail="grammar not associated with that lesson")

    db_lesson.grammars.remove(db_grammar)
    db.commit()

    return {"message" : "grammar deleted"}



# SQLAlchemy supplies is_active=True during INSERT because of the column default
#i don't need to set is_active a value during sqlalchemy instance construction sqlalchemy supplies is active=true during insert
@app.post("/discussion_topics",response_model=PublicDiscussionTopic)
def create_discussion_topic(discussiontopic:CreateDiscussionTopic,current_user:User = Depends(get_current_admin),db :Session = Depends(get_db)):
    db_discussiontopic = DiscussionTopic(title=discussiontopic.title,description=discussiontopic.description)
    db.add(db_discussiontopic)
    db.commit()
    db.refresh(db_discussiontopic)
    return db_discussiontopic

@app.get("/discussion_topics",response_model=list[PublicDiscussionTopic])
def admin_get_all_discussion_topics(db :Session = Depends(get_db),current_user:User = Depends(get_current_admin)):
    db_discussiontopics = db.query(DiscussionTopic).all()
    return db_discussiontopics

@app.get("/discussion_topics/{discussion_topic_id}",response_model=PublicDiscussionTopic)
def admin_get_one_discussion_topic(discussion_topic_id:int,db: Session = Depends(get_db),current_user:User = Depends(get_current_admin)):
    db_discussiontopic = db.query(DiscussionTopic).filter(DiscussionTopic.id == discussion_topic_id).first()
    if not db_discussiontopic:
        raise HTTPException(status_code=404,detail="Discussion topic not found")
    return db_discussiontopic

@app.patch("/discussion_topics/{discussion_topic_id}/discussion_topic",response_model=PublicDiscussionTopic)
def admin_update_a_discussion_topic(discussion_topic_id:int,discussion_topic:UpdateDiscussionTopic,current_user:User = Depends(get_current_admin),
                                    db :Session = Depends(get_db)):
    db_discussiontopic = db.query(DiscussionTopic).filter(DiscussionTopic.id == discussion_topic_id).first()
    if not db_discussiontopic:
        raise HTTPException(status_code=404,detail="Discussion topic not found")
    discussiontopic_data = discussion_topic.model_dump(exclude_unset=True)
    for key,value in discussiontopic_data.items():
        setattr(db_discussiontopic,key,value)
    db.commit()
    db.refresh(db_discussiontopic)
    return db_discussiontopic

@app.delete("/discussion_topics/{discussion_topic_id}")
def delete_a_discussion_topic(discussion_topic_id:int,db :Session = Depends(get_db),current_user:User = Depends(get_current_admin)):

    db_discussiontopic = db.query(DiscussionTopic).filter(DiscussionTopic.id == discussion_topic_id).first()
    if not db_discussiontopic:
        raise HTTPException(status_code=404,detail="Discussion topic not found")

    db_existing_discussiontopic = db.query(DiscussionTopic).filter(DiscussionTopic.id == db_discussiontopic.id,
                                                      DiscussionTopic.studentdiscussion_votes.
                                                      any(StudentDiscussionVote.discussion_topic_id == db_discussiontopic.id)  |
                                                      DiscussionTopic.discussion_sessions.
                                                      any(DiscussionSession.chosen_topic_id == db_discussiontopic.id)  |
                                                      DiscussionTopic.offered_sessions.any() ).first()
    if db_existing_discussiontopic:
        raise HTTPException(status_code=409,detail="Discussion topic already associated with either a discussion session or a discussion vote")
    db.delete(db_discussiontopic)
    db.commit()
    return {"message":"discussion topic deleted successfully"}


@app.post("/discussionsessions/discussion_session",response_model=PublicDiscussionSession)
def create_a_discussion_session(discussion_session:CreateDiscussionSession,current_user:User = Depends(get_current_admin),
                                db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)

    if discussion_session.scheduled_end_at <= discussion_session.scheduled_start_at:
        raise HTTPException(status_code=400,detail="scheduled_end_at must be after scheduled_start_at")

    if discussion_session.voting_closes_at > discussion_session.scheduled_start_at:
        raise HTTPException( status_code=400,detail="voting_closes_at must not be after scheduled_start_at")

    if discussion_session.registration_closes_at > discussion_session.scheduled_start_at:
        raise HTTPException(status_code=400,detail="registration_closes_at must not be after scheduled_start_at")

    if current_time >= discussion_session.voting_closes_at:
        raise HTTPException(status_code=400,detail="voting_closes_at must be in the future")

    if current_time >= discussion_session.registration_closes_at:
        raise HTTPException(status_code=400, detail="registration_closes_at must be in the future")

    if discussion_session.participant_limit <= 0:
        raise HTTPException(status_code=400,detail="participant_limit must be positive")

    if discussion_session.registration_closes_at >= discussion_session.voting_closes_at:
        raise HTTPException(status_code=400,detail="registration_closes_at must be before voting_closes_at")

    db_discussion_session = DiscussionSession(chosen_topic_id = None,scheduled_start_at=discussion_session.scheduled_start_at,
                           scheduled_end_at=discussion_session.scheduled_end_at,actual_started_at=None,actual_ended_at=None,
                           status="scheduled",participant_limit=discussion_session.participant_limit,
                           voting_closes_at=discussion_session.voting_closes_at,
                           registration_closes_at=discussion_session.registration_closes_at)

    db.add(db_discussion_session)
    db.commit()
    db.refresh(db_discussion_session)
    return db_discussion_session


@app.get("/discussionsessions",response_model=list[PublicDiscussionSession])
def user_get_all_discussion_sessions(db: Session = Depends(get_db)):
    db_discussionsessions = db.query(DiscussionSession).all()
    return db_discussionsessions


@app.get("/discussionsessions/{discussion_session_id}",response_model=PublicDiscussionSession)
def user_get_one_discussion_session(discussion_session_id:int,db :Session = Depends(get_db)):
    db_discussionsession = db.query(DiscussionSession).filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussionsession:
        raise HTTPException(status_code=404,detail="Discussion session not found")
    return db_discussionsession


# i implemented with_for_update() to coordinate with concurrent requests on the same row
#so if another admin wants to assign actual_start_at or actual_end_at or even cancell the same discussion session row ,row lock really matters
#we could use request model to determine whether a non null value is provided by the client
#but using dictionary determines whether a value is provided by the client it can be either a null or not null value
#if chosen_topic_id is included in dictionary correctly detects whether the client supplied that field, regardless of whether its value is an integer or None.
#for not nullable columns in database i configure if statement if the key parameter of dictionary is null i raised exception
@app.patch("/discussionsessions/{discussion_session_id}/discussion_session",response_model=PublicDiscussionSession)
def admin_update_a_discussion_session(discussion_session_id:int,discussion_session:UpdateDiscussionSession,current_user:User = Depends(get_current_admin),
                                db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)
    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
              raise HTTPException(status_code=404,detail="Discussion session not found")

    discussion_session_data = discussion_session.model_dump(exclude_unset=True)

    if current_time >= db_discussion_session.scheduled_start_at:
              raise HTTPException(status_code=409,detail="update is not permitted after scheduled start time")
    
    if "chosen_topic_id" in discussion_session_data and discussion_session_data["chosen_topic_id"] is not None:
      if current_time < db_discussion_session.voting_closes_at:
             raise HTTPException(status_code=409,detail="chosen_topic_id cannot be changed before voting closes")


    if "chosen_topic_id" in discussion_session_data and discussion_session_data["chosen_topic_id"] is not None:
        db_already_offered_for_that_discussion_session = (db.query(DiscussionSession).filter(DiscussionSession.id == db_discussion_session.id,
                                                 DiscussionSession.offered_topics.any(DiscussionTopic.id == discussion_session_data["chosen_topic_id"])).first())

        if not db_already_offered_for_that_discussion_session:
             raise HTTPException(status_code=404,detail="Discussion topic has not been offered for that discussion session")


    if  (  "scheduled_start_at" in discussion_session_data and discussion_session_data["scheduled_start_at"] is None or
        "scheduled_end_at" in discussion_session_data and discussion_session_data["scheduled_end_at"] is None or
        "participant_limit" in discussion_session_data and discussion_session_data["participant_limit"] is None or
        "registration_closes_at" in discussion_session_data and discussion_session_data["registration_closes_at"] is None or
        "voting_closes_at" in discussion_session_data and discussion_session_data["voting_closes_at"] is None  or
         "chosen_topic_id" in discussion_session_data and discussion_session_data["chosen_topic_id"] is None):
              raise HTTPException(status_code=400,detail="try again and pass appropriate date and time ")

    for key,value in discussion_session_data.items():
        setattr(db_discussion_session,key,value)

    if db_discussion_session.scheduled_start_at >= db_discussion_session.scheduled_end_at:
        raise HTTPException(
            status_code=400,
            detail="scheduled_start_at must be before scheduled_end_at")

    if db_discussion_session.participant_limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="participant_limit must be positive")

    if db_discussion_session.voting_closes_at >= db_discussion_session.scheduled_start_at:
        raise HTTPException(
            status_code=400,
            detail="voting_closes_at must be before scheduled_start_at")

    if db_discussion_session.voting_closes_at >= db_discussion_session.scheduled_end_at:
        raise HTTPException(
            status_code=400,
            detail="voting_closes_at must be before scheduled_end_at")

    if db_discussion_session.registration_closes_at >= db_discussion_session.scheduled_start_at:
        raise HTTPException(
            status_code=400,
            detail="registration_closes_at must be before scheduled_start_at")

    if db_discussion_session.registration_closes_at >= db_discussion_session.scheduled_end_at:
        raise HTTPException(
            status_code=400,
            detail="registration_closes_at must be before scheduled_end_at")

    if db_discussion_session.registration_closes_at >= db_discussion_session.voting_closes_at:
        raise HTTPException(
            status_code=400,
            detail="registration_closes_at must be before voting_closes_at")

    if db_discussion_session.scheduled_start_at <= current_time:
        raise HTTPException(
            status_code=400,
            detail="scheduled_start_at must be in the future")

    if db_discussion_session.registration_closes_at <= current_time:
        raise HTTPException(
            status_code=400,
            detail="registration_closes_at must be in the future")

    if db_discussion_session.voting_closes_at <= current_time:
        raise HTTPException(
            status_code=400,
            detail="voting_closes_at must be in the future")

    try:
           db.commit()
    except IntegrityError:
           db.rollback()
           raise HTTPException(status_code=409,detail="a database constraint violation occurred")

    db.refresh(db_discussion_session)
    return db_discussion_session


@app.delete("/discussionsessions/{discussion_session_id}")
def delete_a_discussion_session(discussion_session_id:int,current_user:User = Depends(get_current_admin),db: Session = Depends(get_db)):

    db_discussionsession = db.query(DiscussionSession).filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussionsession:
        raise HTTPException(status_code=404,detail="Discussion session not found")
    db_existing_discussionsession = db.query(DiscussionSession).filter(DiscussionSession.id == db_discussionsession.id,
                                    DiscussionSession.studentdiscussion_votes.
                                    any(StudentDiscussionVote.discussion_session_id == db_discussionsession.id)  |
                                    DiscussionSession.discussion_registrations.
                                    any(FreeDiscussionRegistration.discussion_session_id == db_discussionsession.id) |
                                    DiscussionSession.discussion_topic.has(DiscussionTopic.id == db_discussionsession.chosen_topic_id) |
                                    DiscussionSession.offered_topics.any()).first()
    if db_existing_discussionsession:
        raise HTTPException(status_code=409,detail="Discussion session already associated with either vote or registration or chosen topic or offered topics")

    db.delete(db_discussionsession)
    db.commit()
    return {"message" : "discussionsession deleted successfully"}

#nested request model allows the admin to provide multiple topics through request body
#at the end sqlalchemy sends insert statement to insert the association row inside the association table
#at the end of relationship based filtering we use association table or many to many relationship to determine whether any discussion session matching that retrieved session is
#already associated with that retrieved topic
#i added duplicate values prevention inside request body before the for loop and select statements
@app.post("/discussion_sessions/{discussion_session_id}/offerd_topics",response_model=PublicDiscussionSessionOfferedTopics)
def assign_a_selected_number_of_topics_to_a_discussion_session(discussion_session_id:int,offered_topics:CreateDiscussionSessionTopicALLTogether,
                                                    current_user:User = Depends(get_current_admin),db: Session = Depends(get_db)):

    db_discussion_session = db.query(DiscussionSession).filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="Discussion session not found")

    offered_topics = offered_topics.options

    list_of_ids=[]

    for i in offered_topics:
        list_of_ids.append(i.discussion_topic_id)

    unique_ids = set(list_of_ids)
    length_of_ids = len(list_of_ids)
    length_of_unique_ids = len(unique_ids)
    if length_of_unique_ids != length_of_ids:
        raise HTTPException(status_code=400,detail="try again and pass unique topic ids")

    for i in offered_topics:
        db_offered_topic = db.query(DiscussionTopic).filter(DiscussionTopic.id == i.discussion_topic_id).first()
        if not db_offered_topic:
            raise HTTPException(status_code=404,detail="Discussion topic not found")


        db_existing_discussion_session = db.query(DiscussionSession).filter(DiscussionSession.id == db_discussion_session.id,
                                                                            DiscussionSession.offered_topics.
                                                                            any(DiscussionTopic.id ==  db_offered_topic.id)).first()
        if  db_existing_discussion_session:
            raise HTTPException(status_code=409,detail="Discussion session already associated with offered topics")

        db_discussion_session.offered_topics.append(db_offered_topic)

    db.commit()
    db.refresh(db_discussion_session)
    return db_discussion_session

#Overlapping requests from the same user: the same user accidentally sends two registration requests for the same session before the first request finishes.
#Concurrent requests from different users: two users try to register for the same session at nearly the same time.
## .with_for_update() tells PostgreSQL to lock the matching discussion session row until the transaction commits or rolls back.
## A concurrent request that needs a conflicting lock on the same row must wait until the first transaction finishes.
###Reactivating an existing cancelled registration
###We deliberately retain the original registration row instead of creating another one.
###this is consistent with database constraint uniquness that ensures a user has one registration row for one particular discussion session
@app.post("/discussion_session_registration/{discussion_session_id}",response_model=PublicDiscussionSessionRegistration)
def user_register_for_a_discussion_session(discussion_session_id:int,current_user:User = Depends(get_current_user),
                                          db : Session = Depends(get_db)):

    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="Discussion session not found")

    current_time = datetime.now(timezone.utc)

    if current_time >= db_discussion_session.registration_closes_at:
        raise HTTPException(status_code=400,detail="Registration deadline for this discussion session has already passed")

    db_existing_registration = db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.discussion_session_id == db_discussion_session.id,
                                                                           FreeDiscussionRegistration.user_id == current_user.id,
                                                                           FreeDiscussionRegistration.status == "approved").first()
    if db_existing_registration:
        raise HTTPException(status_code=409,detail="this user already registered for this discussion session")

    number_of_registrations_for_this_discussion_session = (db.query(FreeDiscussionRegistration).
                                      filter(FreeDiscussionRegistration.discussion_session_id == db_discussion_session.id,
                                             FreeDiscussionRegistration.status == "approved").count())

    if number_of_registrations_for_this_discussion_session >= db_discussion_session.participant_limit:
        raise HTTPException(status_code=400,detail="Registration participant limit has reached")

    db_existing_cancelled_registration_for_this_discussion_session = (db.query(FreeDiscussionRegistration).
                                                                      filter(FreeDiscussionRegistration.discussion_session_id == db_discussion_session.id,
                                                                                  FreeDiscussionRegistration.status == "cancelled",
                                                                                  FreeDiscussionRegistration.user_id == current_user.id).first())
    if db_existing_cancelled_registration_for_this_discussion_session:
        db_existing_cancelled_registration_for_this_discussion_session.status = "approved"
        db_existing_cancelled_registration_for_this_discussion_session.registered_at = current_time
        db_existing_cancelled_registration_for_this_discussion_session.cancelled_at = None

        user_last_activity_at = helper_function_update_user_last_activity(current_user)

        db.commit()
        return db_existing_cancelled_registration_for_this_discussion_session


    else:
        db_discussion_session_registration = FreeDiscussionRegistration(discussion_session_id=db_discussion_session.id,
                                                                    user_id=current_user.id,registered_at=current_time,
                                                                    status="approved",cancelled_at=None)
        db.add(db_discussion_session_registration)


        user_last_activity_at = helper_function_update_user_last_activity(current_user)

        db.commit()
        return db_discussion_session_registration


#db.refresh in the middle applies to a situation when the same client accidentally sends overlapping requests and calls the same endpoint twice accidentally
#then db.refresh update the status for the overlapping request
# .with_for_update() tells PostgreSQL to lock the matching discussion session row until the transaction commits or rolls back.
# Concurrent registration or cancellation requests for the same session must wait until the first transaction finishes.
@app.post("/cancellation_of_a_discussion_session_registration/{discussion_session_registration_id}",response_model=PublicDiscussionSessionRegistration)
def user_cancel_his_discussion_session_registration(discussion_session_registration_id:int,current_user:User = Depends(get_current_user),
                                                    db: Session = Depends(get_db)):

    db_discussion_session_registration = db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.id == discussion_session_registration_id).first()
    if not db_discussion_session_registration:
        raise HTTPException(status_code=404,detail="registration not found")

    if db_discussion_session_registration.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="user not allowed to perform this action")

    db_discussion_session_id = db_discussion_session_registration.discussion_session_id
    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == db_discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    db.refresh(db_discussion_session_registration)

    if db_discussion_session_registration.status == "cancelled":
        raise HTTPException(status_code=409,detail="the registration has already been cancelled")

    current_time = datetime.now(timezone.utc)
    if  ( db_discussion_session.scheduled_start_at - timedelta(days=2) ) <= current_time:
        raise HTTPException(status_code=409, detail="Discussion session cancellation already passed deadline")


    db_discussion_session_registration.status="cancelled"
    db_discussion_session_registration.cancelled_at = current_time

    user_last_activity_at = helper_function_update_user_last_activity(current_user)

    db.commit()
    db.refresh(db_discussion_session_registration)
    return db_discussion_session_registration

#the last query from the association table reperesenting many to many relationship to determine is there any
#discussion topic matching retrieved topic for this retrieved discussion session or not
@app.post("/discussion_vote/{discission_session_id}/{discussion_topic_id}",response_model=PublicStudentDiscussionVote)
def user_vote_for_a_discussion_topic_offered_in_a_discussion_session(discussion_session_id:int,discussion_topic_id:int,
                                                                      current_user:User = Depends(get_current_user),db: Session = Depends(get_db)):

    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    db_already_registered_for_discussion_session_before_voting = (db.query(FreeDiscussionRegistration).
                                                                  filter(
                                                                 FreeDiscussionRegistration.discussion_session_id == db_discussion_session.id,
                                                                          FreeDiscussionRegistration.user_id == current_user.id,
                                                                           FreeDiscussionRegistration.status == "approved").first())
    if not db_already_registered_for_discussion_session_before_voting:
        raise HTTPException(status_code=403, detail="user has not registered for this discussion session yet")

    current_time = datetime.now(timezone.utc)
    if db_discussion_session.voting_closes_at <= current_time:
        raise HTTPException(status_code=409,detail="voting for this discussion session has already been closed")

    db_discussion_topic =db.query(DiscussionTopic).filter(DiscussionTopic.id == discussion_topic_id).first()
    if not db_discussion_topic:
        raise HTTPException(status_code=404,detail="discussion topic not found")

    db_existing_vote = db.query(StudentDiscussionVote).filter(StudentDiscussionVote.discussion_session_id == db_discussion_session.id,
                                                              StudentDiscussionVote.user_id == current_user.id).first()
    if db_existing_vote:
        raise HTTPException(status_code=409,detail="user has already voted for this discussion session")

    db_topic_offered_for_this_discussion_session = (db.query(DiscussionSession).filter(DiscussionSession.id == db_discussion_session.id,
                                                                                       DiscussionSession.offered_topics.
                                                                                      any(DiscussionTopic.id == db_discussion_topic.id)).first())
    if not db_topic_offered_for_this_discussion_session:
        raise HTTPException(status_code=404,detail="discussion topic has not been offered for this discussion session")

    db_discussion_vote = StudentDiscussionVote(discussion_session_id=db_discussion_session.id,discussion_topic_id=db_discussion_topic.id,
                                            user_id=current_user.id,created_at=current_time)
    db.add(db_discussion_vote)

    user_last_activity_at = helper_function_update_user_last_activity(current_user)

    db.commit()
    db.refresh(db_discussion_vote)
    return db_discussion_vote


#for winning vote initially i assigned the first tuple in the returned list as the winning tuple
#then at each itertion we check the second value of each tuple and compare it with second value of winning tuple
#You initialize winning_topic with the first tuple and compare each tuple's second value against the current winner's second value.
#query returns a list of tuples each tuple's first value represents topic_id and second value represents number of votes per topic
#if there was no vote sqlalchemy returns an empty list
#python loops through each tuple and compare the number of votes of each tuple with winning one if votes are equal compare tuple's id
#winning tuple might change and at the end python extracts the topic_id or first value of of winning tupil
#with_for_update to coordinate concurrent requests i used this sqlalchemy method on the same discussion session row inside user's endpoint
#navigating from vote to user whose registration status is approved and whose registration belongs that discussion session so if the client
#cancells his registration his vote will be excluded from counting
@app.post("/discussion_sessions/{discussion_session_id}/number_of_votes_per_topic_for_discussion_session",response_model=PublicDiscussionSession)
def admin_get_number_of_votes_per_topic_and_manually_select_winning_topic(discussion_session_id:int,db :Session = Depends(get_db),
                                        current_user:User = Depends(get_current_admin)):
    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    current_time = datetime.now(timezone.utc)
    if db_discussion_session.voting_closes_at >= current_time:
        raise HTTPException(status_code=409,detail="voting for this discussion session has not been closed")

    number_of_votes_per_topic = (db.query(StudentDiscussionVote.discussion_topic_id, func.count(StudentDiscussionVote.id)).
                                group_by(StudentDiscussionVote.discussion_topic_id).
                                filter(StudentDiscussionVote.discussion_session_id == db_discussion_session.id,
                                                StudentDiscussionVote.user.has(User.discussion_registrations.
                                               any(  (FreeDiscussionRegistration.status == "approved") &
                                                    (FreeDiscussionRegistration.discussion_session_id == db_discussion_session.id))   )).all())

    if not number_of_votes_per_topic:
        raise HTTPException(status_code=409,detail="no vote has been cast for this discussion session")

    winning_tuple = number_of_votes_per_topic[0]
    for i in number_of_votes_per_topic:
        if ( i[1] > winning_tuple[1] ) or (i[1] == winning_tuple[1] and i[0] < winning_tuple[0]) :
            winning_tuple = i
        else:
            winning_tuple = winning_tuple

    winning_topic_id = winning_tuple[0]

    db_discussion_session.chosen_topic_id = winning_topic_id
    db.commit()
    db.refresh(db_discussion_session)
    return db_discussion_session



@app.post("/discussion_session/{discussion_session_id}/actual_start_at",response_model=PublicDiscussionSession)
def admin_assigns_actual_starting_point_of_discussion_session(discussion_session_id:int,current_user:User = Depends(get_current_admin),
                                                              db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)
    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    if db_discussion_session.scheduled_start_at > current_time:
        raise HTTPException(status_code=409,detail="scheduled start time has not reached")

    if db_discussion_session.actual_started_at is not None:
        raise HTTPException(status_code=409,detail="actual start at already has been assigned")

    if db_discussion_session.status != "scheduled":
        raise HTTPException(status_code=409,detail="discussion session is not scheduled")

    db_discussion_session.actual_started_at = current_time
    db_discussion_session.status ="in_progress"

    db.commit()
    db.refresh(db_discussion_session)
    return db_discussion_session



@app.post("/discussion_session/{discussion_session_id}/actual_end_at",response_model=PublicDiscussionSession)
def admin_assign_actual_ending_point_of_discussion_session(discussion_session_id:int,current_user:User = Depends(get_current_admin),
                                                            db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)

    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    if db_discussion_session.actual_ended_at is not None:
        raise HTTPException(status_code=409,detail="actual end at already has been assigned")

    if db_discussion_session.status != "in_progress":
        raise HTTPException(status_code=409,detail="discussion session is not in_progress")

    db_discussion_session.actual_ended_at = current_time
    db_discussion_session.status = "completed"

    db.commit()
    db.refresh(db_discussion_session)
    return db_discussion_session


@app.post("/discussion_session/{discussion_session_id}/cancellation")
def admin_cancel_a_discussion_session(discussion_session_id:int,current_user:User = Depends(get_current_admin),
                                      db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)

    db_discussion_session = db.query(DiscussionSession).with_for_update().filter(DiscussionSession.id == discussion_session_id).first()
    if not db_discussion_session:
        raise HTTPException(status_code=404,detail="discussion session not found")

    if db_discussion_session.status != "scheduled":
        raise HTTPException(status_code=409,detail="discussion session is not scheduled")

    if ( db_discussion_session.scheduled_start_at - timedelta(days=2) ) <= current_time:
        raise HTTPException(status_code=409,detail="cancellation deadline has passed")

    db_discussion_session.status = "cancelled"
    db.commit()
    db.refresh(db_discussion_session)
    return {"message" : "discussion session successfully canceled"}



##### list_of_current_month_and_previous_six_month = [beginning_of_this_month]
##previous_month = beginning_of_this_month
 ##  for i in range(6):
#if previous_month.month == 1:
##previous_month = previous_month.replace(year=previous_month.year - 1,month=12,
##           day=1,hour=0,minute=0,second=0,microsecond=0)
##else:
#previous_month = previous_month.replace(year=previous_month.year,month=previous_month.month - 1,
#                            hour=0,minute=0,second=0,microsecond=0)
#list_of_current_month_and_previous_six_month.append(previous_month)

@app.get("/chart_of_study_time/chart",response_model=list[PublicChartStudyTimeRecord])
def user_get_charts_of_study_time(period:str,db: Session = Depends(get_db),current_user:User = Depends(get_current_user)):

    if period == "hourly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_tomorrow = beginning_of_today + timedelta(days=1)

        list_of_twenty_four_hours_fall_within_today = [beginning_of_today]
        beginning_of_next_hour = beginning_of_today



        for i in range(23):
            beginning_of_next_hour = beginning_of_next_hour + timedelta(minutes=60)
            list_of_twenty_four_hours_fall_within_today.append(beginning_of_next_hour)

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_tomorrow,
                                                          StudySession.ended_at > beginning_of_today,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.status == "completed",
                                                          StudySession.ended_at != None).all()


        list_of_study_time_for_each_hour = []


        for h in list_of_twenty_four_hours_fall_within_today:
            beginning_of_following_hour = h + timedelta(minutes=60)

            this_hour_study_time = 0
            before_this_hour_study_time = 0
            after_this_hour_study_time = 0

            for s in db_study_sessions:
                if s.started_at >= h and s.ended_at <= beginning_of_following_hour:
                    duration_minutes = ( s.ended_at - s.started_at ).total_seconds() / 60
                    this_hour_study_time = duration_minutes + this_hour_study_time

                elif s.started_at < h and s.ended_at > h and s.ended_at <= beginning_of_following_hour:
                    duration_minutes = ( h - s.started_at ).total_seconds() / 60
                    before_this_hour_study_time = duration_minutes + before_this_hour_study_time
                    duration_minutes = ( s.ended_at - h ).total_seconds() / 60
                    this_hour_study_time = duration_minutes + this_hour_study_time

                elif s.started_at >= h and s.ended_at > beginning_of_following_hour and s.started_at < beginning_of_following_hour:
                    duration_minutes = ( s.ended_at - beginning_of_following_hour ).total_seconds() / 60
                    after_this_hour_study_time = duration_minutes + after_this_hour_study_time
                    duration_minutes = ( beginning_of_following_hour - s.started_at).total_seconds() / 60
                    this_hour_study_time = duration_minutes + this_hour_study_time

                elif s.started_at < h and s.ended_at > beginning_of_following_hour:
                    duration_minutes = ( h - s.started_at ).total_seconds() / 60
                    before_this_hour_study_time = duration_minutes + before_this_hour_study_time
                    duration_minutes = ( beginning_of_following_hour - h ).total_seconds() / 60
                    this_hour_study_time = duration_minutes + this_hour_study_time
                    duration_minutes = ( s.ended_at - beginning_of_following_hour ).total_seconds() / 60
                    after_this_hour_study_time = duration_minutes + after_this_hour_study_time

            total_study_time_of_each_hour = this_hour_study_time
            list_of_study_time_for_each_hour.append( {"date" : h.date() , "study_time" : int(total_study_time_of_each_hour) ,"hour" : h.hour } )

        return list_of_study_time_for_each_hour


    if period == "daily":
       today = datetime.now(timezone.utc)
       beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
       beginning_of_tomorrow = beginning_of_today + timedelta(days=1)
       beginning_of_seven_days_ago = beginning_of_today - timedelta(days=6)

       db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_tomorrow,
                                                      StudySession.ended_at > beginning_of_seven_days_ago,
                                                      StudySession.user_id == current_user.id,
                                                      StudySession.status == "completed",
                                                      StudySession.ended_at != None).all()


       days = [ beginning_of_today,beginning_of_today - timedelta(days=1),
             beginning_of_today - timedelta(days=2),beginning_of_today - timedelta(days=3),
             beginning_of_today - timedelta(days=4),
            beginning_of_today - timedelta(days=5),beginning_of_today - timedelta(days=6)]

       list_of_study_times_for_each_day = []

       for i in days:
           today_study_time = 0
           before_today_study_time = 0
           after_today_study_time = 0

           for j in db_study_sessions:
               if j.started_at >= i and j.ended_at <= i + timedelta(days=1):
                  duration_minutes = ( j.ended_at - j.started_at ).total_seconds() / 60
                  today_study_time = duration_minutes + today_study_time

               elif j.started_at < i and j.ended_at <= i + timedelta(days=1) and j.ended_at > i :
                  duration_minutes = ( i - j.started_at ).total_seconds() / 60
                  before_today_study_time = duration_minutes + before_today_study_time
                  duration_minutes = ( j.ended_at - i ).total_seconds() / 60
                  today_study_time = duration_minutes + today_study_time

               elif j.started_at >= i and j.ended_at > i + timedelta(days=1) and j.started_at < i + timedelta(days=1):
                  duration_minutes = ( j.ended_at - ( i + timedelta(days=1) ) ).total_seconds() / 60
                  after_today_study_time = duration_minutes + after_today_study_time
                  duration_minutes = ( ( i + timedelta(days=1) ) - j.started_at ).total_seconds() / 60
                  today_study_time = duration_minutes + today_study_time

               elif j.started_at < i and j.ended_at > i + timedelta(days=1):
                  duration_minutes = ( i - j.started_at ).total_seconds() / 60
                  before_today_study_time = duration_minutes + before_today_study_time
                  duration_minutes = ( ( i + timedelta(days=1) ) - i ).total_seconds() / 60
                  today_study_time = duration_minutes + today_study_time
                  duration_minutes = ( j.ended_at -  ( i + timedelta(days=1)) ).total_seconds() / 60
                  after_today_study_time = duration_minutes + after_today_study_time


           total_study_time_of_each_day = today_study_time
           list_of_study_times_for_each_day.append( {"date" : i.date(),"study_time" : int(total_study_time_of_each_day) } )

       return list_of_study_times_for_each_day


    elif period == "weekly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_week = beginning_of_today - timedelta(days=beginning_of_today.weekday())
        beginning_of_six_weeks_ago = beginning_of_this_week - timedelta(weeks=6)
        beginning_of_next_week = beginning_of_this_week + timedelta(weeks=1)


        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_week,
                                                          StudySession.ended_at > beginning_of_six_weeks_ago,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.status == "completed",
                                                          StudySession.ended_at != None).all()

        weeks = [ beginning_of_this_week,beginning_of_this_week - timedelta(weeks=1),beginning_of_this_week - timedelta(weeks=2),
                  beginning_of_this_week - timedelta(weeks=3),beginning_of_this_week - timedelta(weeks=4),
                  beginning_of_this_week - timedelta(weeks=5),beginning_of_this_week - timedelta(weeks=6)]

        list_of_study_times_for_each_week = []



        for i in weeks:
            this_week_study_time = 0
            before_this_week_study_time = 0
            after_this_week_study_time = 0

            for j in db_study_sessions:
                if j.started_at >= i and j.ended_at <= i + timedelta(weeks=1):
                    duration_minutes = ( j.ended_at - j.started_at ).total_seconds() / 60
                    this_week_study_time = duration_minutes + this_week_study_time

                elif j.started_at < i and j.ended_at <= i + timedelta(weeks=1) and j.ended_at > i :
                    duration_minutes = ( i - j.started_at ).total_seconds() / 60
                    before_this_week_study_time = duration_minutes + before_this_week_study_time
                    duration_minutes = ( j.ended_at - i ).total_seconds() / 60
                    this_week_study_time = duration_minutes + this_week_study_time

                elif j.started_at >= i and j.ended_at > i + timedelta(weeks=1) and j.started_at < i + timedelta(weeks=1):
                    duration_minutes = ( j.ended_at - ( i + timedelta(weeks=1) ) ).total_seconds() / 60
                    after_this_week_study_time = duration_minutes + after_this_week_study_time
                    duration_minutes = ( ( i + timedelta(weeks=1) ) - j.started_at ).total_seconds() / 60
                    this_week_study_time = duration_minutes + this_week_study_time

                elif j.started_at < i and j.ended_at > i + timedelta(weeks=1):
                    duration_minutes = ( i - j.started_at ).total_seconds() / 60
                    before_this_week_study_time = duration_minutes + before_this_week_study_time
                    duration_minutes = ( ( i + timedelta(weeks=1) ) - i ).total_seconds() / 60
                    this_week_study_time = duration_minutes + this_week_study_time
                    duration_minutes = ( j.ended_at - ( i + timedelta(weeks=1) ) ).total_seconds() / 60
                    after_this_week_study_time = duration_minutes + after_this_week_study_time

            total_study_time_of_each_week = this_week_study_time
            list_of_study_times_for_each_week.append({ "date" : i.date(),"study_time" : int(total_study_time_of_each_week) })

        return list_of_study_times_for_each_week

    elif period == "monthly":

        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_month = beginning_of_today - ( timedelta(beginning_of_today.day - 1 ) )

        if beginning_of_this_month.month == 12:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year + 1,month=1,day=1,
                                                                      hour=0,minute=0,second=0,microsecond=0)
        else:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year,month=beginning_of_this_month.month + 1,
                                                                      day=1,hour=0,minute=0,second=0,microsecond=0)

        list_of_current_month_and_the_previous_six_months = [beginning_of_this_month]
        beginning_of_previous_month = beginning_of_this_month

        for i in range(6):
            if beginning_of_previous_month.month == 1:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year - 1,month=12,
                                                                     day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year,
                                                                     month=beginning_of_previous_month.month - 1,
                                                                     day=1,hour=0,minute=0,second=0,microsecond=0)

            list_of_current_month_and_the_previous_six_months.append(beginning_of_previous_month)


        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_month,
                                                          StudySession.ended_at > list_of_current_month_and_the_previous_six_months[6] ,
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.status == "completed",
                                                          StudySession.ended_at != None).all()

        list_of_study_times_for_each_month = []


        for m in list_of_current_month_and_the_previous_six_months:
            if m.month == 12:
                beginning_of_following_month = m.replace(year=m.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                beginning_of_following_month = m.replace(year=m.year,month=m.month + 1,day=1,hour=0,minute=0,second=0,microsecond=0)

            this_month_study_time = 0
            before_this_month_study_time = 0
            after_this_month_study_time = 0

            for s in db_study_sessions:
                if s.started_at >= m and s.ended_at <= beginning_of_following_month:
                    duration_minutes = ( s.ended_at - s.started_at ).total_seconds() / 60
                    this_month_study_time = duration_minutes + this_month_study_time

                elif s.started_at < m and s.ended_at > m and s.ended_at <= beginning_of_following_month:
                    duration_minutes = ( m - s.started_at ).total_seconds() / 60
                    before_this_month_study_time = duration_minutes + before_this_month_study_time
                    duration_minutes = ( s.ended_at - m ).total_seconds() / 60
                    this_month_study_time = duration_minutes + this_month_study_time

                elif s.started_at >= m and s.ended_at > beginning_of_following_month and s.started_at < beginning_of_following_month:
                    duration_minutes = ( s.ended_at - beginning_of_following_month ).total_seconds() / 60
                    after_this_month_study_time = duration_minutes + after_this_month_study_time
                    duration_minutes = ( beginning_of_following_month - s.started_at ).total_seconds() / 60
                    this_month_study_time = duration_minutes + this_month_study_time

                elif s.started_at < m and s.ended_at > beginning_of_following_month:
                    duration_minutes = ( m - s.started_at ).total_seconds() / 60
                    before_this_month_study_time = duration_minutes + before_this_month_study_time
                    duration_minutes = ( beginning_of_following_month - m ).total_seconds() / 60
                    this_month_study_time = duration_minutes + this_month_study_time
                    duration_minutes = ( s.ended_at - beginning_of_following_month ).total_seconds() / 60
                    after_this_month_study_time = duration_minutes + after_this_month_study_time

            total_study_time_of_each_month = this_month_study_time
            list_of_study_times_for_each_month.append( {"date" : m.date() , "study_time" : int(total_study_time_of_each_month)} )


        return list_of_study_times_for_each_month


    elif period == "yearly":

        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_year = beginning_of_today.replace(year=beginning_of_today.year,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        beginning_of_next_year = beginning_of_this_year.replace(year=beginning_of_this_year.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)

        list_of_current_year_and_previous_six_years = [beginning_of_this_year]
        beginning_of_previous_year = beginning_of_this_year

        for i in range(6):
            beginning_of_previous_year = beginning_of_previous_year.replace(year=beginning_of_previous_year.year - 1,month=1,day=1,
                                                                            hour=0,minute=0,second=0,microsecond=0)

            list_of_current_year_and_previous_six_years.append(beginning_of_previous_year)

        db_study_sessions = db.query(StudySession).filter(StudySession.started_at < beginning_of_next_year,
                                                          StudySession.ended_at > list_of_current_year_and_previous_six_years[6],
                                                          StudySession.user_id == current_user.id,
                                                          StudySession.status == "completed",
                                                          StudySession.ended_at != None).all()

        list_of_study_times_for_each_year = []

        for y in list_of_current_year_and_previous_six_years:

            beginning_of_following_year = y.replace(year=y.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)

            this_year_study_time = 0
            before_this_year_study_time = 0
            after_this_year_study_time = 0

            for s in db_study_sessions:
                if s.started_at >= y and s.ended_at <= beginning_of_following_year:
                    duration_minutes = ( s.ended_at - s.started_at ).total_seconds() / 60
                    this_year_study_time = duration_minutes + this_year_study_time

                elif s.started_at < y and s.ended_at > y and s.ended_at <= beginning_of_following_year:
                    duration_minutes = ( y - s.started_at ).total_seconds() / 60
                    before_this_year_study_time = duration_minutes + before_this_year_study_time
                    duration_minutes = ( s.ended_at - y ).total_seconds() / 60
                    this_year_study_time = duration_minutes + this_year_study_time

                elif s.started_at >= y and s.ended_at > beginning_of_following_year and s.started_at < beginning_of_following_year:
                    duration_minutes = ( s.ended_at - beginning_of_following_year ).total_seconds() / 60
                    after_this_year_study_time = duration_minutes + after_this_year_study_time
                    duration_minutes = ( beginning_of_following_year - s.started_at ).total_seconds() / 60
                    this_year_study_time = duration_minutes + this_year_study_time

                elif s.started_at < y and s.ended_at > beginning_of_following_year:
                    duration_minutes = ( y - s.started_at ).total_seconds() / 60
                    before_this_year_study_time = duration_minutes + before_this_year_study_time
                    duration_minutes = ( beginning_of_following_year - y ).total_seconds() / 60
                    this_year_study_time = duration_minutes + this_year_study_time
                    duration_minutes =( s.ended_at - beginning_of_following_year ).total_seconds() / 60
                    after_this_year_study_time = duration_minutes + after_this_year_study_time

            total_study_time_of_each_year = this_year_study_time
            list_of_study_times_for_each_year.append( { "date": y.date(), "study_time": int(total_study_time_of_each_year) } )

        return list_of_study_times_for_each_year




@app.get("/quiz_performance/chart",response_model=list[PublicChartQuizPerformanceRecord])
def user_get_charts_of_quiz_performance(period:str,current_user:User = Depends(get_current_user),db: Session = Depends(get_db)):
    if period == "daily":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_tomorrow = beginning_of_today + timedelta(days=1)

        list_of_current_day_and_the_previous_six_days = [beginning_of_today]
        beginning_of_previous_day = beginning_of_today

        for i in range(6):
            beginning_of_previous_day = beginning_of_previous_day - timedelta(days=1)
            list_of_current_day_and_the_previous_six_days.append(beginning_of_previous_day)

        db_answers = db.query(Answer).filter(Answer.user_id == current_user.id,
                                           Answer.created_at < beginning_of_tomorrow,
                                             Answer.created_at >= list_of_current_day_and_the_previous_six_days[6] ).all()

        daily_quiz_performance = []


        for d in list_of_current_day_and_the_previous_six_days:
            beginning_of_following_day = d + timedelta(days=1)

            number_of_correct_answers = 0
            number_of_incorrect_answers = 0
            number_of_all_answers = 0

            for a in db_answers:

               if   d <= a.created_at < beginning_of_following_day:
                   number_of_all_answers = 1 + number_of_all_answers

                   if  a.correctness == True:
                          number_of_correct_answers = 1 + number_of_correct_answers

                   else:
                          number_of_incorrect_answers = 1 + number_of_incorrect_answers

            if number_of_all_answers == 0:
                accuracy_percentage_of_each_day = None

            else:
                accuracy_percentage_of_each_day = ( number_of_correct_answers / number_of_all_answers ) * 100

            daily_quiz_performance.append({"number_of_correct_answers" : number_of_correct_answers,
                                                             "number_of_incorrect_answers" : number_of_incorrect_answers,
                                                             "number_of_all_answers" : number_of_all_answers,
                                                             "accuracy_percentage" : accuracy_percentage_of_each_day,
                                                             "date" : d.date()})
        return daily_quiz_performance

    elif period == "weekly":

        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_week = beginning_of_today - timedelta(days=beginning_of_today.weekday())
        beginning_of_next_week = beginning_of_this_week + timedelta(weeks=1)

        list_of_beginning_of_current_week_and_the_previous_six_weeks = [beginning_of_this_week]
        beginning_of_previous_week = beginning_of_this_week

        for i in range(6):
            beginning_of_previous_week = beginning_of_previous_week - timedelta(weeks=1)
            list_of_beginning_of_current_week_and_the_previous_six_weeks.append(beginning_of_previous_week)

        db_answers = db.query(Answer).filter(Answer.user_id == current_user.id,
                                             Answer.created_at < beginning_of_next_week,
                                             Answer.created_at >= list_of_beginning_of_current_week_and_the_previous_six_weeks[6] ).all()


        weekly_quiz_performance = []

        for w in list_of_beginning_of_current_week_and_the_previous_six_weeks:
            beginning_of_following_week = w + timedelta(weeks=1)

            number_of_this_week_answers = 0
            number_of_correct_answers = 0
            number_of_incorrect_answers = 0

            for a in db_answers:
                if a.created_at >= w and a.created_at < beginning_of_following_week:
                    number_of_this_week_answers = number_of_this_week_answers + 1

                    if a.correctness == True:
                        number_of_correct_answers = number_of_correct_answers + 1
                    else:
                        number_of_incorrect_answers = number_of_incorrect_answers + 1

            if number_of_this_week_answers == 0:
                accuracy_percentage_of_each_week = None
            else:
                accuracy_percentage_of_each_week = ( number_of_correct_answers / number_of_this_week_answers ) * 100

            weekly_quiz_performance.append( { "number_of_all_answers" : number_of_this_week_answers,
                                              "number_of_correct_answers" : number_of_correct_answers,
                                              "number_of_incorrect_answers" : number_of_incorrect_answers,
                                              "accuracy_percentage" : accuracy_percentage_of_each_week,
                                              "date" : w.date() } )
        return weekly_quiz_performance


    elif period == "monthly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_month = beginning_of_today - timedelta(days=beginning_of_today.day - 1 )

        if beginning_of_this_month.month == 12:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year + 1,
                                                                      month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        else:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year,
                                                                      month=beginning_of_this_month.month + 1,
                                                                      day=1,hour=0,minute=0,second=0,microsecond=0)

        list_of_current_month_and_previous_six_month = [beginning_of_this_month]
        beginning_of_previous_month = beginning_of_this_month

        for i in range(6):
            if beginning_of_previous_month.month == 1:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year - 1,
                                                                                  month=12,day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year,
                                                                                  month=beginning_of_previous_month.month - 1,
                                                                                  day=1,hour=0,minute=0,second=0,microsecond=0)

            list_of_current_month_and_previous_six_month.append(beginning_of_previous_month)



        db_answers = db.query(Answer).filter(Answer.user_id == current_user.id,
                                             Answer.created_at < beginning_of_next_month,
                                             Answer.created_at >= list_of_current_month_and_previous_six_month[6] ).all()


        monthly_quiz_performance = []

        for m in list_of_current_month_and_previous_six_month:
            if m.month == 12:
                beginning_of_following_month = m.replace(year=m.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
            else:
                beginning_of_following_month = m.replace(year=m.year,month=m.month + 1,day=1,hour=0,minute=0,second=0,microsecond=0)

            number_of_this_month_answers = 0
            number_of_correct_answers = 0
            number_of_incorrect_answers = 0

            for a in db_answers:
                if a.created_at >= m and a.created_at < beginning_of_following_month:
                    number_of_this_month_answers = number_of_this_month_answers + 1
                    if a.correctness == True:
                        number_of_correct_answers = number_of_correct_answers + 1
                    else:
                        number_of_incorrect_answers = number_of_incorrect_answers + 1


            if number_of_this_month_answers == 0:
                accuracy_percentage_of_each_month = None
            else:
                accuracy_percentage_of_each_month = ( number_of_correct_answers / number_of_this_month_answers ) * 100

            monthly_quiz_performance.append( { "number_of_all_answers" : number_of_this_month_answers,
                                               "number_of_correct_answers" : number_of_correct_answers,
                                               "number_of_incorrect_answers" : number_of_incorrect_answers,
                                               "accuracy_percentage" : accuracy_percentage_of_each_month,
                                               "date" : m.date()} )

        return monthly_quiz_performance


    elif period == "yearly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_year = beginning_of_today.replace( year=today.year,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        beginning_of_next_year = beginning_of_this_year.replace(year=beginning_of_this_year.year + 1,month=1,day=1,
                                                                hour=0,minute=0,second=0,microsecond=0)

        list_of_current_year_and_previous_six_years = [beginning_of_this_year]
        beginning_of_previous_year = beginning_of_this_year

        for i in range(6):
            beginning_of_previous_year = beginning_of_previous_year.replace(year=beginning_of_previous_year.year - 1,
                                                                            month=1,day=1,hour=0,minute=0,second=0,microsecond=0)

            list_of_current_year_and_previous_six_years.append(beginning_of_previous_year)

        db_answers = db.query(Answer).filter(Answer.user_id == current_user.id,
                                             Answer.created_at < beginning_of_next_year,
                                             Answer.created_at >= list_of_current_year_and_previous_six_years[6] ).all()


        yearly_quiz_performance = []

        for y in list_of_current_year_and_previous_six_years:
            beginning_of_following_year = y.replace(year=y.year + 1,month=1,day=1,hour=0,minute=0,second=0,microsecond=0)

            number_of_this_year_answers = 0
            number_of_correct_answers = 0
            number_of_incorrect_answers = 0

            for a in db_answers:
                if a.created_at >= y and a.created_at < beginning_of_following_year:
                    number_of_this_year_answers = number_of_this_year_answers + 1
                    if a.correctness == True:
                        number_of_correct_answers = number_of_correct_answers + 1
                    else:
                        number_of_incorrect_answers = number_of_incorrect_answers + 1

            if number_of_this_year_answers == 0:
                accuracy_percentage_of_each_year = None

            else:
                accuracy_percentage_of_each_year = ( number_of_correct_answers / number_of_this_year_answers ) * 100


            yearly_quiz_performance.append( { "number_of_all_answers" : number_of_this_year_answers,
                                              "number_of_correct_answers" : number_of_correct_answers,
                                               "number_of_incorrect_answers" : number_of_incorrect_answers,
                                                "accuracy_percentage" :accuracy_percentage_of_each_year,
                                                 "date" : y.date() } )
        return yearly_quiz_performance



@app.get("/free_discussion_registration/chart",response_model=list[PublicChartFreeDiscussionRegistrationCancellationReport])
def user_get_chart_of_free_discussion_registration(period:str,current_user:User = Depends(get_current_user),db: Session = Depends(get_db)):

    if period == "daily":

      today = datetime.now(timezone.utc)
      beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
      beginning_of_tomorrow = beginning_of_today + timedelta(days=1)

      list_of_beginning_of_current_day_and_previous_six_days = [beginning_of_today]
      beginning_of_previous_day = beginning_of_today

      for i in range(6):
          beginning_of_previous_day = beginning_of_previous_day - timedelta(days=1)
          list_of_beginning_of_current_day_and_previous_six_days.append(beginning_of_previous_day)

      db_free_discussion_registrations = (db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.user_id == current_user.id,
                                             (  FreeDiscussionRegistration.registered_at < beginning_of_tomorrow ) &
                                             (  FreeDiscussionRegistration.registered_at >= list_of_beginning_of_current_day_and_previous_six_days[6] )
                                                                                    |
                                             (  FreeDiscussionRegistration.cancelled_at < beginning_of_tomorrow ) &
                                             (   FreeDiscussionRegistration.cancelled_at >= list_of_beginning_of_current_day_and_previous_six_days[6] )   ) .all())



      daily_registration_cancellation_report = []

      for d in list_of_beginning_of_current_day_and_previous_six_days:
           beginning_of_following_day = d + timedelta(days=1)

           number_of_registrations_in_this_day = 0
           number_of_cancellations_in_this_day = 0
           number_of_registration_cancellation_activities_in_this_day = 0

           for r in db_free_discussion_registrations:
              if d <= r.registered_at < beginning_of_following_day:
                 number_of_registration_cancellation_activities_in_this_day = 1 + number_of_registration_cancellation_activities_in_this_day
                 number_of_registrations_in_this_day = 1 + number_of_registrations_in_this_day

              if  r.cancelled_at is not None and d <= r.cancelled_at < beginning_of_following_day:
                  number_of_cancellations_in_this_day = 1 + number_of_cancellations_in_this_day
                  number_of_registration_cancellation_activities_in_this_day = 1 + number_of_registration_cancellation_activities_in_this_day

           daily_registration_cancellation_report.append( { "number_of_all_registration_cancellation_activities" : number_of_registration_cancellation_activities_in_this_day,
                                                         "number_of_registration_activity" : number_of_registrations_in_this_day,
                                                         "number_of_cancellation_activity" : number_of_cancellations_in_this_day,
                                                         "date" : d.date() } )

      return daily_registration_cancellation_report

    elif period == "weekly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_week = beginning_of_today - timedelta(days=beginning_of_today.weekday())
        beginning_of_next_week = beginning_of_this_week + timedelta(days=7)

        list_of_current_week_and_the_previous_six_weeks = [beginning_of_this_week]
        beginning_of_previous_week = beginning_of_this_week

        for i in range(6):
            beginning_of_previous_week = beginning_of_previous_week - timedelta(days=7)
            list_of_current_week_and_the_previous_six_weeks.append(beginning_of_previous_week)

        db_free_discussion_registrations = db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.user_id == current_user.id,
                                                                (FreeDiscussionRegistration.registered_at < beginning_of_next_week) &
                                                                 (FreeDiscussionRegistration.registered_at >= list_of_current_week_and_the_previous_six_weeks[6])
                                                                                       |
                                                                (FreeDiscussionRegistration.cancelled_at < beginning_of_next_week) &
                                                                (FreeDiscussionRegistration.cancelled_at >= list_of_current_week_and_the_previous_six_weeks[6])
                                                                                       ).all()

        weekly_registration_cancellation_report = []
        for w in list_of_current_week_and_the_previous_six_weeks:
            beginning_of_following_week = w + timedelta(days=7)

            number_of_registrations_in_this_week = 0
            number_of_cancellations_in_this_week = 0
            number_of_registration_cancellation_activities_in_this_week = 0

            for r in db_free_discussion_registrations:
                if w <= r.registered_at < beginning_of_following_week:
                    number_of_registrations_in_this_week = 1 + number_of_registrations_in_this_week
                    number_of_registration_cancellation_activities_in_this_week = 1 + number_of_registration_cancellation_activities_in_this_week

                if  r.cancelled_at is not None and w <= r.cancelled_at < beginning_of_following_week:
                    number_of_cancellations_in_this_week = 1 + number_of_cancellations_in_this_week
                    number_of_registration_cancellation_activities_in_this_week = 1 + number_of_registration_cancellation_activities_in_this_week

            weekly_registration_cancellation_report.append( { "number_of_all_registration_cancellation_activities" : number_of_registration_cancellation_activities_in_this_week,
                                                         "number_of_registration_activity" : number_of_registrations_in_this_week,
                                                         "number_of_cancellation_activity" :number_of_cancellations_in_this_week,
                                                         "date" : w.date() } )
        return weekly_registration_cancellation_report

    elif period == "monthly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_month = beginning_of_today - timedelta(days=beginning_of_today.day - 1 )
        if beginning_of_this_month.month == 12:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year + 1,month=1,
                                                                      day=1,minute=0,second=0,microsecond=0)
        else:
            beginning_of_next_month = beginning_of_this_month.replace(year=beginning_of_this_month.year,month=beginning_of_this_month.month + 1,
                                                                      day=1,minute=0,second=0,microsecond=0)

        list_of_current_month_and_the_previous_six_month = [beginning_of_this_month]
        beginning_of_previous_month = beginning_of_this_month

        for i in range(6):
            if beginning_of_previous_month.month == 1:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year - 1,month=12,
                                                                                  day=1,minute=0,second=0,microsecond=0)
            else:
                beginning_of_previous_month = beginning_of_previous_month.replace(year=beginning_of_previous_month.year,
                                                                                  month=beginning_of_previous_month.month - 1,
                                                                                  day=1,minute=0,second=0,microsecond=0)

            list_of_current_month_and_the_previous_six_month.append(beginning_of_previous_month)

        db_free_discussion_registrations = db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.user_id == current_user.id,
                                                     ( ( FreeDiscussionRegistration.registered_at < beginning_of_next_month ) &
                                                        ( FreeDiscussionRegistration.registered_at >= list_of_current_month_and_the_previous_six_month[6] )  )
                                                                                                    |
                                                     (  ( FreeDiscussionRegistration.cancelled_at < beginning_of_next_month ) &
                                                        ( FreeDiscussionRegistration.cancelled_at >= list_of_current_month_and_the_previous_six_month[6] )  )
                                                                                       ).all()


        monthly_registration_cancellation_report = []

        for m in list_of_current_month_and_the_previous_six_month:
            if m.month == 12:
                beginning_of_following_month = m.replace(year=m.year + 1,month=1,day=1,minute=0,second=0,microsecond=0)
            else:
                beginning_of_following_month = m.replace(year=m.year,month=m.month + 1,day=1,minute=0,second=0,microsecond=0)


            number_of_registrations_in_this_month = 0
            number_of_registration_cancellation_activities_in_this_month = 0
            number_of_cancellations_in_this_month = 0

            for r in db_free_discussion_registrations:
                if m <= r.registered_at < beginning_of_following_month:
                        number_of_registrations_in_this_month = 1 + number_of_registrations_in_this_month
                        number_of_registration_cancellation_activities_in_this_month = 1 + number_of_registration_cancellation_activities_in_this_month

                if  r.cancelled_at is not None and  m <=  r.cancelled_at < beginning_of_following_month:
                        number_of_cancellations_in_this_month = 1 + number_of_cancellations_in_this_month
                        number_of_registration_cancellation_activities_in_this_month = 1 + number_of_registration_cancellation_activities_in_this_month

            monthly_registration_cancellation_report.append( { "number_of_all_registration_cancellation_activities" : number_of_registration_cancellation_activities_in_this_month,
                                                         "number_of_registration_activity" : number_of_registrations_in_this_month,
                                                         "number_of_cancellation_activity" :number_of_cancellations_in_this_month,
                                                         "date" : m.date() } )

        return monthly_registration_cancellation_report

    elif period == "yearly":
        today = datetime.now(timezone.utc)
        beginning_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        beginning_of_this_year = beginning_of_today.replace(year=beginning_of_today.year,month=1,day=1,minute=0,second=0,microsecond=0)
        beginning_of_next_year = beginning_of_this_year.replace(year=beginning_of_this_year.year + 1,month=1,day=1,minute=0,second=0,microsecond=0)

        list_of_beginning_of_current_year_and_previous_six_years = [beginning_of_this_year]
        beginning_of_previous_year = beginning_of_this_year

        for i in range(6):
            beginning_of_previous_year = beginning_of_previous_year.replace(year=beginning_of_previous_year.year - 1,month=1,day=1,minute=0,second=0,microsecond=0)
            list_of_beginning_of_current_year_and_previous_six_years.append(beginning_of_previous_year)

        db_free_discussion_registrations = db.query(FreeDiscussionRegistration).filter(FreeDiscussionRegistration.user_id == current_user.id,
                                                        (   (FreeDiscussionRegistration.registered_at < beginning_of_next_year ) &
                                                             (FreeDiscussionRegistration.registered_at >= list_of_beginning_of_current_year_and_previous_six_years[6])  )
                                                                                       |
                                                        (     (FreeDiscussionRegistration.cancelled_at < beginning_of_next_year) &
                                                             (FreeDiscussionRegistration.cancelled_at >= list_of_beginning_of_current_year_and_previous_six_years[6])   )
                                                                                       ) .all()

        yearly_registration_cancellation_report = []

        for y in list_of_beginning_of_current_year_and_previous_six_years:
            beginning_of_following_year = y.replace(year=y.year + 1,month=1,day=1,minute=0,second=0,microsecond=0)

            number_of_registrations_in_this_year = 0
            number_of_registration_cancellation_activities_in_this_year = 0
            number_of_cancellations_in_this_year = 0

            for r in db_free_discussion_registrations:
                if  y <= r.registered_at < beginning_of_following_year:
                    number_of_registrations_in_this_year = 1 + number_of_registrations_in_this_year
                    number_of_registration_cancellation_activities_in_this_year = 1 + number_of_registration_cancellation_activities_in_this_year

                if r.cancelled_at is not None and y <= r.cancelled_at < beginning_of_following_year:
                    number_of_cancellations_in_this_year = 1 + number_of_cancellations_in_this_year
                    number_of_registration_cancellation_activities_in_this_year = 1 + number_of_registration_cancellation_activities_in_this_year

            yearly_registration_cancellation_report.append( { "number_of_all_registration_cancellation_activities" : number_of_registration_cancellation_activities_in_this_year,
                                                         "number_of_registration_activity" : number_of_registrations_in_this_year,
                                                         "number_of_cancellation_activity" :number_of_cancellations_in_this_year,
                                                         "date" : y.date() } )

        return yearly_registration_cancellation_report



@app.get("/lesson_progresses/{lesson_id}",response_model=PublicLessonProgress)
def user_get_lesson_progress(lesson_id:int,current_user:User = Depends(get_current_user),db:Session = Depends(get_db)):
    db_lesson = db.query(Lesson).filter(Lesson.id == lesson_id,Lesson.course.has(Course.users.any(User.id == current_user.id))).first()
    if db_lesson is None:
        raise HTTPException(status_code=404,detail="lesson not found or you are not authorized")

    sections = db_lesson.sections

    number_of_covered_sections = 0
    for s in sections:
        study_session_for_each_section = db.query(StudySession).filter(StudySession.lesson_id == db_lesson.id,
                                                                       StudySession.status == "completed",
                                                                       StudySession.user_id == current_user.id,
                                                                     StudySession.section_id == s.id).first()
        if study_session_for_each_section is not None:
            number_of_covered_sections = 1 + number_of_covered_sections
        else:
            number_of_covered_sections = 0 + number_of_covered_sections

    if len(sections) == 0:
        raise HTTPException(status_code=404,detail="lesson has no associated sections")

    total_percentage_of_all_sections_coverage = ( number_of_covered_sections /  len(sections) ) * 100

    existing_entire_lesson_study_session = db.query(StudySession).filter(StudySession.lesson_id == db_lesson.id,
                                                                         StudySession.status == "completed",
                                                                         StudySession.user_id == current_user.id,
                                                                         StudySession.section_id.is_(None)).first()
    if existing_entire_lesson_study_session is not None:
        total_percentage_of_all_sections_coverage = 100


    number_of_completed_study_sessions_for_this_lesson_belonging_to_user = (db.query(StudySession).
                                                                             filter(StudySession.lesson_id == db_lesson.id,
                                                                                        StudySession.user_id == current_user.id,
                                                                                        StudySession.status == "completed").count())

    return {"sections_coverage_percentage" : total_percentage_of_all_sections_coverage,
            "number_of_completed_study_sessions" : number_of_completed_study_sessions_for_this_lesson_belonging_to_user}

























































































































































