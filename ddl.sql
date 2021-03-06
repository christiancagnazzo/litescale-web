create table _User (
    Email varchar(100),
    Password varchar(200),
    primary key (Email)
);

create table Project (
    ProjectId integer AUTO_INCREMENT,
    ProjectName varchar(35),
    Phenomenon varchar(35) not null,
    TupleSize integer not null,
    ReplicateInstances integer not null,
    ProjectOwner varchar(100),
    primary key (ProjectId),
    foreign key (ProjectOwner) references _User(Email) on update cascade on delete cascade
);

create table Authorization (
    Project integer,
    Authorized varchar(100),
    primary key (Project, Authorized),
    foreign key (Project) references Project(ProjectId) on update cascade on delete cascade,
    foreign key (Authorized) references _User(Email) on update cascade on delete cascade
);

create table Instance (
    InstanceId varchar(100),
    InstanceDescription varchar(500) not null,
    Project integer,
    primary key (InstanceId, Project),
    foreign key (Project) references Project(ProjectId) on update cascade on delete cascade
);

create table Tuple (
    TupleId integer,
    Project integer,
    primary key (TupleId, Project),
    foreign key (Project) references Instance(Project) on update cascade on delete cascade
);

create table InstanceTuple (
    Instance varchar(100),
    Tuple integer,
    Project integer,
    primary key (Instance, Tuple, Project),
    foreign key (Instance, Project) references Instance(InstanceId, Project) on update cascade on delete cascade,
    foreign key (Tuple, Project) references Tuple(TupleId, Project) on update cascade on delete cascade
);

create table Annotation (
    AnnotationId integer AUTO_INCREMENT,
    Best varchar(100),
    Worst varchar(100),
    Tuple integer,
    Annotator varchar(100),
    Project integer,
    primary key (AnnotationId),
    foreign key (Annotator) references _User(Email) on update cascade on delete cascade,
    foreign key (Tuple, Project) references Tuple(TupleId, Project) on update cascade on delete cascade,
    foreign key (Best, Project) references Instance(InstanceId, Project) on update cascade on delete cascade,
    foreign key (Worst, Project) references Instance(InstanceId, Project) on update cascade on delete cascade,
    unique (Tuple, Annotator, Project)
);






